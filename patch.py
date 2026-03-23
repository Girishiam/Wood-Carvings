content = open('frontend/src/App.jsx', encoding='utf-8').read()

old_div = '                 <div className="flex-1 flex items-center justify-center overflow-auto">'
new_div = '                 <div className="flex-1 min-h-0 flex items-center justify-center overflow-hidden bg-white p-2">'
content = content.replace(old_div, new_div, 1)

old_cls = 'className="max-w-full max-h-full object-contain"'
new_cls = 'style={{ maxWidth: "100%", maxHeight: "100%", width: "100%", height: "auto", objectFit: "contain", display: "block" }}'
content = content.replace(old_cls, new_cls, 1)

open('frontend/src/App.jsx', 'w', encoding='utf-8').write(content)
print('Patched OK')
