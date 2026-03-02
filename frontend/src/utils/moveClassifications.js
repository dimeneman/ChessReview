import bestImg from '../images/classification/best.png';
import blunderImg from '../images/classification/blunder.png';
import brilliantImg from '../images/classification/brilliant.png';
import bookImg from '../images/classification/theory.png'; // Using theory for book
import greatImg from '../images/classification/great.png'; // Correctly import great.png
import excellentImg from '../images/classification/excellent.png';
import forcedImg from '../images/classification/forced.png';
import goodImg from '../images/classification/good.png';
import inaccuracyImg from '../images/classification/inaccuracy.png';
import missImg from '../images/classification/miss.png';
import mistakeImg from '../images/classification/mistake.png';
import theoryImg from '../images/classification/theory.png';

export function getClassificationStyle(label) {
    if (!label) return null;

    switch (label) {
        case "Brilliant":
            return { img: brilliantImg, color: "#1baca6", label: "Brilliant" };
        case "Great":
            // Explicitly map "Great" to the great.png image
            return { img: greatImg, color: "#5c8bb0", label: "Great" };
        case "Best":
            return { img: bestImg, color: "#95b645", label: "Best" };
        case "Excellent":
            return { img: excellentImg, color: "#96bc4b", label: "Excellent" };
        case "Good":
            return { img: goodImg, color: "#96bc4b", label: "Good" };
        case "Inaccuracy":
            return { img: inaccuracyImg, color: "#f0c15c", label: "Inaccuracy" };
        case "Mistake":
            return { img: mistakeImg, color: "#e6912c", label: "Mistake" };
        case "Blunder":
            return { img: blunderImg, color: "#ca3431", label: "Blunder" };
        case "Missed Win":
            return { img: missImg, color: "#e6912c", label: "Missed Win" };
        case "Missed Mate":
            return { img: missImg, color: "#e6912c", label: "Missed Mate" };
        case "Theory":
            return { img: theoryImg, color: "#b38865", label: "Theory" };
        case "Book":
            return { img: bookImg, color: "#b38865", label: "Book" };
        case "Forced":
            return { img: forcedImg, color: "#96bc4b", label: "Forced" };
        default:
            return { img: null, color: "#gray-400", label: label };
    }
}
