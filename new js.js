document.addEventListener("DOMContentLoaded", function () {

  /* ===============================
     SHARED SCROLL ENGINE
  =============================== */

  let ticking = false;

  function onScroll() {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        updateHistory();
        updateObjCards();
        updateDirCards();
        ticking = false;
      });
      ticking = true;
    }
  }

  window.addEventListener('scroll', onScroll);


 /* ===============================
   1. LATAR BELAKANG (HISTORY)
=============================== */

const historySection = document.querySelector('#pj-history-01');
const historyBlocks = historySection
  ? historySection.querySelectorAll('.pj-block')
  : [];
const historyImage = historySection
  ? historySection.querySelector('.pj-image')
  : null;

let historyIndex = -1;

function updateHistory() {
  if (!historySection || !historyBlocks.length || !historyImage) return;

  let closest = 0;
  let minOffset = Infinity;
  const center = window.innerHeight / 2;

  historyBlocks.forEach((block, index) => {
    const rect = block.getBoundingClientRect();
    const blockCenter = rect.top + rect.height / 2;
    const offset = Math.abs(blockCenter - center);

    if (offset < minOffset) {
      minOffset = offset;
      closest = index;
    }
  });

  // no change → do nothing
  if (closest === historyIndex) return;

  const active = historyBlocks[closest];
  const newImg = active.dataset.img;

  // do NOT override if invalid
  if (!newImg) return;

  // prevent duplicate updates
  if (historyImage.dataset.current === newImg) {
    historyIndex = closest;
    return;
  }

  // update state FIRST
  historyIndex = closest;
  historyImage.dataset.current = newImg;

  /* ===============================
   POP ANIMATION (VISIBLE)
=============================== */

// remove old class first
historyImage.classList.remove("pop");

// force reflow (IMPORTANT — makes animation restart)
void historyImage.offsetWidth;

// change image
historyImage.style.backgroundImage = `url("${newImg}")`;

// add pop effect
historyImage.classList.add("pop");

// remove pop after animation
setTimeout(() => {
  historyImage.classList.remove("pop");
}, 400);

  // active state
  historyBlocks.forEach(b => b.classList.remove('active'));
  active.classList.add('active');
}

  /* ===============================
     2. OBJEKTIF (INTERSECTION)
  =============================== */

  const objSection = document.querySelector('.pj-objektif-section');
  const objItems = objSection ? objSection.querySelectorAll('.pj-obj-item') : [];

  if (objSection) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {

          const index = [...objItems].indexOf(entry.target);

          setTimeout(() => {
            entry.target.classList.add('show');
          }, index * 120);

        }
      });
    }, { threshold: 0.2 });

    objItems.forEach(item => observer.observe(item));
  }


  /* ===============================
     3. OBJEKTIF CARDS (SCROLL)
  =============================== */

  const obj2Section = document.querySelector('#pj-obj-02');
  const objCards = obj2Section ? obj2Section.querySelectorAll('.pj-obj2-card') : [];

  let objIndex = -1;

  function updateObjCards() {
    if (!obj2Section || !objCards.length) return;

    let closest = 0;
    let minOffset = Infinity;
    const center = window.innerHeight / 2;

    objCards.forEach((card, index) => {
      const rect = card.getBoundingClientRect();
      const cardCenter = rect.top + rect.height / 2;
      const offset = Math.abs(cardCenter - center);

      if (offset < minOffset) {
        minOffset = offset;
        closest = index;
      }
    });

    if (closest !== objIndex) {
      objIndex = closest;
      objCards.forEach(c => c.classList.remove('active'));
      objCards[objIndex].classList.add('active');
    }
  }


  /* ===============================
     4. DIRECTORY
  =============================== */

  const dirSection = document.querySelector('#pj-dir-04');
  const dirCards = dirSection ? dirSection.querySelectorAll('.pj-dir4-card') : [];

  let dirIndex = -1;

  function updateDirCards() {
    if (!dirSection || !dirCards.length) return;

    let closest = 0;
    let minOffset = Infinity;
    const center = window.innerHeight / 2;

    dirCards.forEach((card, index) => {
      const rect = card.getBoundingClientRect();
      const cardCenter = rect.top + rect.height / 2;
      const offset = Math.abs(cardCenter - center);

      if (offset < minOffset) {
        minOffset = offset;
        closest = index;
      }
    });

    if (closest !== dirIndex) {
      dirIndex = closest;
      dirCards.forEach(c => c.classList.remove('active'));
      dirCards[dirIndex].classList.add('active');
    }
  }


  /* ===============================
     INITIAL RUN
  =============================== */

  updateHistory();
  updateObjCards();
  updateDirCards();

});

