import React from 'react';

// Using standard Wikimedia Commons SVG images for the classic chess look

const PieceImg = ({ squareWidth, src }) => (
    <div
        style={{
            width: squareWidth,
            height: squareWidth,
            backgroundImage: `url(${src})`,
            backgroundSize: '100%',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center'
        }}
    />
);

const wP = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg" />;
const wN = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg" />;
const wB = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg" />;
const wR = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/7/72/Chess_rlt45.svg" />;
const wQ = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg" />;
const wK = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/4/42/Chess_klt45.svg" />;

const bP = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_pdt45.svg" />;
const bN = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg" />;
const bB = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg" />;
const bR = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg" />;
const bQ = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_qdt45.svg" />;
const bK = (props) => <PieceImg {...props} src="https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg" />;

export const CUSTOM_PIECES = {
    wP, wN, wB, wR, wQ, wK,
    bP, bN, bB, bR, bQ, bK
};
