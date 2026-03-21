const track2 = document.querySelector('.slider__track2');
const prevBtn2 = document.querySelector('.slider__arrow2--left');
const nextBtn2 = document.querySelector('.slider__arrow2--right');

let cards2 = document.querySelectorAll('.card2');

// === 1. Клонируем крайние карточки ===
const firstClone2 = cards2[0].cloneNode(true); // Исправлено: cards2 вместо cards
const lastClone2 = cards2[cards2.length - 1].cloneNode(true); // Исправлено: cards2 вместо cards

track2.appendChild(firstClone2);
track2.insertBefore(lastClone2, cards2[0]);

// Обновляем список карточек после клонирования
cards2 = document.querySelectorAll('.card2');

// === 2. Начальный индекс (первая реальная карточка) ===
let index2 = 1;

// === 3. Ширина карточки (учёт gap + margin) ===
function getCardWidth2() { // Добавлен суффикс 2
  const card2 = cards2[0];
  const style2 = getComputedStyle(card2);
  const margin2 = parseInt(style2.marginLeft) + parseInt(style2.marginRight); // Исправлено: style2
  const gap = 20; // gap из .slider__track
  return card2.offsetWidth + margin2 + gap; // Исправлено: card2 и margin2
}

// === 4. Устанавливаем стартовую позицию ===
track2.style.transition = 'none';
track2.style.transform = `translateX(-${index2 * getCardWidth2()}px)`; // Исправлено: index2 и getCardWidth2()

// === 5. Следующий слайд ===
function nextSlide2() { // Добавлен суффикс 2
  index2++;
  track2.style.transition = 'transform 0.5s ease';
  track2.style.transform = `translateX(-${index2 * getCardWidth2()}px)`; // Исправлено: index2 и getCardWidth2()

  // Телепорт с клона на первый реальный элемент
  if (index2 === cards2.length - 7) {
    setTimeout(() => {
      track2.style.transition = 'none';
      index2 = 1;
      track2.style.transform = `translateX(-${index2 * getCardWidth2()}px)`; // Исправлено
    }, 500);
  }
}

// === 6. Предыдущий слайд ===
function prevSlide2() { // Добавлен суффикс 2
  index2--;
  track2.style.transition = 'transform 0.5s ease';
  track2.style.transform = `translateX(-${index2 * getCardWidth2()}px)`; // Исправлено: index2 и getCardWidth2()

  // Телепорт с клона на последний реальный элемент
  if (index2 === 0) {
    setTimeout(() => {
      track2.style.transition = 'none';
      index2 = cards2.length - 2;
      track2.style.transform = `translateX(-${index2 * getCardWidth2()}px)`; // Исправлено
    }, 500);
  }
}

// === 7. Кнопки ===
nextBtn2.addEventListener('click', nextSlide2); // Исправлено: nextSlide2
prevBtn2.addEventListener('click', prevSlide2); // Исправлено: prevSlide2

// === 8. Автопрокрутка ===
let autoSlide2 = setInterval(nextSlide2, 3000); // Исправлено: nextSlide2 и autoSlide2

// (опционально) пауза при наведении
track2.addEventListener('mouseenter', () => clearInterval(autoSlide2)); // Исправлено: autoSlide2
track2.addEventListener('mouseleave', () => {
  autoSlide2 = setInterval(nextSlide2, 3000); // Исправлено: autoSlide2 и nextSlide2
});

// === 9. Пересчёт при ресайзе ===
window.addEventListener('resize', () => {
  track2.style.transition = 'none';
  track2.style.transform = `translateX(-${index2 * getCardWidth2()}px)`; // Исправлено: index2 и getCardWidth2()
});
