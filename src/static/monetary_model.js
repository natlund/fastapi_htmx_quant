let timerID = null;

function startAnimation() {
    if (timerID == null) {
        timerID = setInterval(moveCircle, 10);
    }
}

function stopAnimation() {
    if (timerID != null) {
        clearInterval(timerID);
        timerID = null;
    }
}

function moveCircle() {
    const circle = document.getElementById("circle4");
    const cx = circle.getAttribute("cx");
    let newCX = parseInt(cx) + 1;
    if (newCX > 600) {
        newCX = 50;
    }
    circle.setAttribute("cx", newCX)
}

document.getElementById("startAnimation").addEventListener("click", startAnimation);
document.getElementById("stopAnimation").addEventListener("click", stopAnimation);