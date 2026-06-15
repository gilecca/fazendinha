// Adicionar ao carrinho via AJAX
document.querySelectorAll('.btn-add-cart').forEach(btn => {
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    const url = this.dataset.url;
    const badge = document.querySelector('.cart-badge');
    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
      }
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        if (badge) {
          badge.textContent = data.count;
          badge.style.display = data.count > 0 ? 'inline' : 'none';
        }
        const original = this.innerHTML;
        this.innerHTML = '✅ Adicionado!';
        this.classList.add('btn-success');
        setTimeout(() => {
          this.innerHTML = original;
          this.classList.remove('btn-success');
        }, 1500);
      }
    });
  });
});

// Scroll automático no chat
const chatBox = document.querySelector('.chat-container');
if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

// Preview de imagem no formulário
document.querySelectorAll('input[type="file"]').forEach(input => {
  input.addEventListener('change', function() {
    const preview = document.querySelector(`#preview-${this.id}`);
    if (preview && this.files[0]) {
      preview.src = URL.createObjectURL(this.files[0]);
      preview.style.display = 'block';
    }
  });
});

// Mostrar/esconder campo farm_name baseado no tipo de usuário
const userTypeRadios = document.querySelectorAll('input[name="user_type"]');
const farmNameGroup = document.querySelector('#farm-name-group');
if (userTypeRadios.length && farmNameGroup) {
  function toggleFarmName() {
    const selected = document.querySelector('input[name="user_type"]:checked');
    farmNameGroup.style.display = selected && selected.value === 'producer' ? 'block' : 'none';
  }
  userTypeRadios.forEach(r => r.addEventListener('change', toggleFarmName));
  toggleFarmName();
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    document.cookie.split(';').forEach(cookie => {
      const c = cookie.trim();
      if (c.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(c.slice(name.length + 1));
      }
    });
  }
  return cookieValue;
}

// Animação de entrada dos cards
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.product-card, .producer-card, .farm-card').forEach(card => {
  card.style.opacity = '0';
  card.style.transform = 'translateY(20px)';
  card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
  observer.observe(card);
});
