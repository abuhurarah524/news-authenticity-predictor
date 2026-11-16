"""Convert the original DOCX into the app's static, readable report page."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil

import mammoth
from lxml import html, etree
from PIL import Image
from build_wbs import PHASES, build as build_wbs

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'


def convert(source):
    assets = WEB / 'report-assets'
    assets.mkdir(exist_ok=True)
    shutil.copyfile(source, assets / 'original-report.docx')
    images = []

    def save_image(image):
        with image.open() as stream:
            data = stream.read()
        extension = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif'}.get(image.content_type)
        if not extension:
            with Image.open(BytesIO(data)) as picture:
                if picture.format == 'WMF':
                    picture.load(dpi=192)
                buffer = BytesIO()
                picture.convert('RGBA').save(buffer, format='PNG')
                data = buffer.getvalue()
            extension = 'png'
        name = 'figure-' + hashlib.sha256(data).hexdigest()[:12] + '.' + extension
        (assets / name).write_bytes(data)
        images.append(name)
        return {'src': 'report-assets/' + name, 'alt': image.alt_text or f'Original report illustration {len(images)}'}

    with source.open('rb') as stream:
        result = mammoth.convert_to_html(stream, convert_image=mammoth.images.img_element(save_image), style_map="""
            p[style-name='Heading 1'] => h2:fresh
            p[style-name='Heading 2'] => h3:fresh
            p[style-name='Heading 3'] => h4:fresh
            p[style-name='Caption'] => p.figure-caption:fresh
            p[style-name='Table of Figures'] => p.figure-index:fresh
            p[style-name='Default'] => p:fresh
            p[style-name='toc 1'] => p.figure-index:fresh
            p[style-name='toc 2'] => p.figure-index:fresh
            p[style-name='toc 3'] => p.figure-index:fresh
            p[style-name='List Paragraph'] => p:fresh
        """)
    content = html.fragment_fromstring(result.value, create_parent='div')
    # Mammoth flattens this grouped Word drawing into fragmented text boxes.
    # Replace only that drawing with the same phase/task hierarchy, rendered as SVG.
    build_wbs()
    for heading in content.xpath('.//h3'):
        if heading.text_content().strip().startswith('3.1 Work breakdown'):
            introduction = heading.getnext()
            node = introduction.getnext()
            while node is not None and not ('Work Breakdown Structure Diagram' in node.text_content() and node.get('class') == 'figure-caption'):
                following = node.getnext()
                node.getparent().remove(node)
                node = following
            if node is None:
                raise ValueError('Could not locate the end of the original work breakdown drawing.')
            figure = html.Element('figure', {'class': 'wbs-figure'})
            viewport = etree.SubElement(figure, 'div', {'class': 'wbs-viewport', 'tabindex': '0', 'role': 'region', 'aria-label': 'Work breakdown diagram; scroll horizontally to see all five phases'})
            etree.SubElement(viewport, 'img', {'src': 'report-assets/work-breakdown.svg', 'alt': 'News Authenticity Predictor work breakdown structure: Research, Design, Implementation, Testing, and Deployment, each with its connected tasks.', 'width': '1140', 'height': '790'})
            link = etree.SubElement(figure, 'a', {'href': 'report-assets/work-breakdown.svg', 'target': '_blank', 'rel': 'noopener noreferrer', 'class': 'wbs-fullscreen'})
            link.text = 'Open full-size diagram ↗'
            details = etree.SubElement(figure, 'details', {'class': 'wbs-outline'})
            etree.SubElement(details, 'summary').text = 'Read the diagram as text'
            outline = etree.SubElement(details, 'ul')
            for phase, tasks in PHASES:
                item = etree.SubElement(outline, 'li')
                etree.SubElement(item, 'strong').text = phase
                children = etree.SubElement(item, 'ul')
                for task in tasks:
                    etree.SubElement(children, 'li').text = task
            introduction.addnext(figure)
            break
    # Add structure to the source's unstyled front matter and appendix headings.
    for paragraph in content.xpath('./p'):
        text = paragraph.text_content().strip()
        if text in ('Abstract', 'Appendix A'):
            paragraph.tag = 'h2'
        if text.startswith('CHAPTER #'):
            paragraph.set('class', 'chapter-divider')
    for index, heading in enumerate(content.xpath('.//h2 | .//h3 | .//h4')):
        heading.set('id', 'section-' + str(index + 1))
    for table in content.xpath('.//table'):
        wrapper = html.Element('div', {'class': 'report-table', 'tabindex': '0', 'role': 'region', 'aria-label': 'Report table'})
        table.addprevious(wrapper)
        wrapper.append(table)
    for image in content.xpath('.//img'):
        image.set('loading', 'lazy')
        image.set('decoding', 'async')
    for link in content.xpath('.//a[@href]'):
        href = link.get('href')
        if href.startswith(('https://', 'http://')):
            link.set('target', '_blank')
            link.set('rel', 'noopener noreferrer')
        elif not href.startswith('#'):
            link.attrib.pop('href')
    body = ''.join(html.tostring(child, encoding='unicode') for child in content)
    from html import escape
    toc_html = ''.join(f'<a class="toc-{heading.tag}" href="#{heading.get("id")}">{escape(heading.text_content().strip())}</a>'
                       for heading in content.xpath('.//h2 | .//h3'))
    words = len(content.text_content().split())
    template = (ROOT / 'scripts/report-template.html').read_text(encoding='utf-8')
    page = template.replace('<!-- REPORT_CONTENT -->', body).replace('<!-- REPORT_TOC -->', toc_html).replace('<!-- REPORT_WORDS -->', f'{words:,}')
    (WEB / 'report.html').write_text(page, encoding='utf-8')
    metadata = {'source': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'words': words, 'tables': len(content.xpath('.//table')), 'images': len(images),
                'headings': len(content.xpath('.//h2 | .//h3 | .//h4')),
                'conversion_messages': [{'type': message.type, 'message': message.message} for message in result.messages]}
    (assets / 'conversion.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    convert(parser.parse_args().source)
