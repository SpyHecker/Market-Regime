import re

with open('templates/documentation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the stray closing </div> right after </table>
html = html.replace('</table>\n                        </div>', '</table>')

# Change trailing </p> that should be </ul>
html = html.replace('</li>\n                            </p>', '</li>\n                            </ul>')

with open('templates/documentation.html', 'w', encoding='utf-8') as f:
    f.write(html)
