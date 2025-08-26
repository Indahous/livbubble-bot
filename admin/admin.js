// admin/admin.js — Полная версия с загрузкой, редактированием, сохранением

let tasks = [];
const tasksList = document.getElementById('tasks-list');

// Загрузка заданий
async function loadTasks() {
  try {
    const response = await fetch('/tasks.json', {
      credentials: 'include' // 🔥 Отправляем куки
    });
    if (!response.ok) throw new Error('Network error');
    const data = await response.json();
    tasks = Array.isArray(data.priority_tasks) ? data.priority_tasks : [];
    renderTasks();
    console.log('✅ Задания загружены:', tasks);
  } catch (error) {
    console.error('❌ Ошибка загрузки заданий:', error);
    tasks = [];
    renderTasks();
    alert('⚠️ Не удалось загрузить задания. Проверьте подключение.');
  }
}

// Отображение всех заданий
function renderTasks() {
  tasksList.innerHTML = '';
  tasks.forEach((task, index) => {
    const taskEl = document.createElement('div');
    taskEl.className = 'task';
    taskEl.innerHTML = `
      <div>
        <input type="text" placeholder="Название" value="${escapeHtml(task.title || '')}" oninput="updateTask(${index}, 'title', this.value)">
        
        <select onchange="updateTask(${index}, 'type', this.value)">
          <option value="subscribe" ${task.type === 'subscribe' ? 'selected' : ''}>Подписаться</option>
          <option value="buy" ${task.type === 'buy' ? 'selected' : ''}>Купить</option>
          <option value="question" ${task.type === 'question' ? 'selected' : ''}>Вопрос</option>
        </select>
        
        <input type="text" placeholder="Ссылка (если есть)" value="${escapeHtml(task.link || '')}" oninput="updateTask(${index}, 'link', this.value)">
        
        <input type="text" placeholder="Правильный ответ (для вопросов)" value="${escapeHtml(task.correct_answer || '')}" oninput="updateTask(${index}, 'correct_answer', this.value)">
      </div>
      <button onclick="removeTask(${index})">🗑️ Удалить</button>
    `;
    tasksList.appendChild(taskEl);
  });
}

// Экранирование HTML (защита от XSS)
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Обновление поля задания
function updateTask(index, field, value) {
  if (tasks[index]) {
    tasks[index][field] = value;
  }
}

// Добавить новое задание
function addTask() {
  tasks.push({
    title: '',
    type: 'question',
    link: '',
    correct_answer: ''
  });
  renderTasks();
  tasksList.lastElementChild.scrollIntoView({ behavior: 'smooth' });
}

// Удалить задание
function removeTask(index) {
  if (confirm('Удалить это задание?')) {
    tasks.splice(index, 1);
    renderTasks();
  }
}

// Сохранить задания
async function saveTasks() {
  const password = prompt("🔒 Введите пароль администратора:");
  if (!password) {
    alert('❌ Отменено пользователем');
    return;
  }

  try {
    const response = await fetch('/save-tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, priority_tasks: tasks }),
      credentials: 'include' // 🔥 Отправляем куки
    });

    const data = await response.json();
    if (data.success) {
      alert('✅ Задания успешно сохранены!');
    } else {
      alert(`❌ ${data.message}`);
    }
  } catch (error) {
    console.error('❌ Ошибка сохранения:', error);
    alert('⚠️ Ошибка сети. Проверьте подключение.');
  }
}

// Загрузка при старте
window.onload = loadTasks;
