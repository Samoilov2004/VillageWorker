const track = document.querySelector('.slider__track');
const prevBtn = document.querySelector('.slider__arrow--left');
const nextBtn = document.querySelector('.slider__arrow--right');

let cards = document.querySelectorAll('.card');

// === 1. Клонируем крайние карточки ===
const firstClone = cards[0].cloneNode(true);
const lastClone = cards[cards.length - 1].cloneNode(true);

track.appendChild(firstClone);
track.insertBefore(lastClone, cards[0]);

// Обновляем список карточек после клонирования
cards = document.querySelectorAll('.card');

// === 2. Начальный индекс (первая реальная карточка) ===
let index = 1;

// === 3. Ширина карточки (учёт gap + margin) ===
function getCardWidth() {
  const card = cards[0];
  const style = getComputedStyle(card);
  const margin =
    parseInt(style.marginLeft) + parseInt(style.marginRight);
  const gap = 20; // gap из .slider__track
  return card.offsetWidth + margin + gap;
}

// === 4. Устанавливаем стартовую позицию ===
track.style.transition = 'none';
track.style.transform = `translateX(-${index * getCardWidth()}px)`;

// === 5. Следующий слайд ===
function nextSlide() {
  index++;
  track.style.transition = 'transform 0.5s ease';
  track.style.transform = `translateX(-${index * getCardWidth()}px)`;

  // Телепорт с клона на первый реальный элемент
  if (index === cards.length - 10) {
    setTimeout(() => {
      track.style.transition = 'none';
      index = 1;
      track.style.transform = `translateX(-${index * getCardWidth()}px)`;
    }, 500);
  }
}

// === 6. Предыдущий слайд ===
function prevSlide() {
  index--;
  track.style.transition = 'transform 0.5s ease';
  track.style.transform = `translateX(-${index * getCardWidth()}px)`;

  // Телепорт с клона на последний реальный элемент
  if (index === 0) {
    setTimeout(() => {
      track.style.transition = 'none';
      index = cards.length - 2;
      track.style.transform = `translateX(-${index * getCardWidth()}px)`;
    }, 500);
  }
}

// === 7. Кнопки ===
nextBtn.addEventListener('click', nextSlide);
prevBtn.addEventListener('click', prevSlide);

// === 8. Автопрокрутка ===
let autoSlide = setInterval(nextSlide, 3000);

// (опционально) пауза при наведении
track.addEventListener('mouseenter', () => clearInterval(autoSlide));
track.addEventListener('mouseleave', () => {
  autoSlide = setInterval(nextSlide, 3000);
});

// === 9. Пересчёт при ресайзе ===
window.addEventListener('resize', () => {
  track.style.transition = 'none';
  track.style.transform = `translateX(-${index * getCardWidth()}px)`;
});

