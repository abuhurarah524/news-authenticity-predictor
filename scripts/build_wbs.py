"""Render the report's Word-shape hierarchy as a readable SVG diagram."""
from html import escape
from pathlib import Path

PHASES = [
    ('Research', ['Research Existing Solution', 'Requirement Gathering', 'Research on Algorithms']),
    ('Design', ['Low Fidelity Diagrams', 'High Fidelity Diagrams', 'Use Case Diagrams', 'Sequence Diagrams', 'Activity Diagrams']),
    ('Implementation', ['Train Text Based Model', 'Front End', 'Back End', 'Integrating Front and Back End', 'Deploying', 'Integrate Back End & Front End']),
    ('Testing', ['Unit Testing', 'Integration Testing', 'System Testing', 'Acceptance Testing']),
    ('Deployment', ['User Manual', 'Marketing']),
]


def lines(label, limit=22):
    result, line = [], ''
    for word in label.split():
        if len(line + ' ' + word) > limit and line:
            result.append(line)
            line = word
        else:
            line = (line + ' ' + word).strip()
    return result + [line]


def build():
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="790" viewBox="0 0 1140 790" role="img" aria-labelledby="title description">',
             '<title id="title">News Authenticity Predictor — Work Breakdown Structure</title>',
             '<desc id="description">Five phases: Research, Design, Implementation, Testing, and Deployment. Each phase connects to its tasks.</desc>',
             '<rect width="1140" height="790" fill="#fffef9"/>',
             '<g font-family="Arial, sans-serif" text-anchor="middle">',
             '<rect x="390" y="24" width="360" height="72" rx="7" fill="#2f4d3e"/>',
             '<text x="570" y="55" font-size="19" fill="#fffef9">News Authenticity</text>',
             '<text x="570" y="79" font-size="19" fill="#fffef9">Predictor</text>',
             '<path d="M570 96V126H120M570 126H1020" fill="none" stroke="#9aaa86" stroke-width="2"/>']
    for index, (phase, tasks) in enumerate(PHASES):
        x = 120 + index * 225
        parts.extend([
            f'<path d="M{x} 126V155" fill="none" stroke="#9aaa86" stroke-width="2"/>',
            f'<rect x="{x-100}" y="155" width="200" height="58" rx="5" fill="#e7edda" stroke="#b6c2a2"/>',
            f'<text x="{x}" y="190" font-size="17" font-weight="bold" fill="#2b4938">{escape(phase)}</text>',
            f'<path d="M{x} 213V233H{x-96}V{275+(len(tasks)-1)*86}" fill="none" stroke="#b0bea0" stroke-width="2"/>',
        ])
        for task_index, task in enumerate(tasks):
            y = 246 + task_index * 86
            parts.extend([
                f'<path d="M{x-96} {y+29}H{x-83}" fill="none" stroke="#b0bea0" stroke-width="2"/>',
                f'<rect x="{x-83}" y="{y}" width="183" height="64" rx="5" fill="#f5f6ef" stroke="#d4dcc8"/>',
            ])
            task_lines = lines(task)
            start = y + 36 - (len(task_lines) - 1) * 10
            for line_index, line in enumerate(task_lines):
                parts.append(f'<text x="{x+8}" y="{start+line_index*20}" font-size="14" fill="#3c503a">{escape(line)}</text>')
    parts.extend(['</g>', '<text x="24" y="768" font-family="Arial, sans-serif" font-size="12" fill="#7c876e">Figure 3 · Original hierarchy redrawn for web readability</text>', '</svg>'])
    target = Path(__file__).resolve().parents[1] / 'web/report-assets/work-breakdown.svg'
    target.parent.mkdir(exist_ok=True)
    target.write_text('\n'.join(parts), encoding='utf-8')


if __name__ == '__main__':
    build()
