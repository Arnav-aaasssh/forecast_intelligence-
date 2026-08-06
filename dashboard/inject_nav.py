with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

nav_function = """
window.nav = function(pageId) {
  document.querySelectorAll('.rail-item').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  
  let p = pageId.replace('page-', '');
  let railItem = document.querySelector(`.rail-item[data-page="${p}"]`);
  if (railItem) railItem.classList.add('active');
  
  document.getElementById(pageId).classList.add('active');
  window.scrollTo(0,0);
  
  const backBtn = document.getElementById('back-nav-btn');
  if (backBtn) {
    backBtn.style.display = (pageId === 'page-exec') ? 'none' : 'block';
  }
}
"""

lines.insert(655, nav_function)

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(''.join(lines))
print('SUCCESS')
