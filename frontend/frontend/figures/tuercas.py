import reflex as rx

def tuercas() -> rx.Component:
    return rx.html(
        """
            <style>
                .bg {
                    padding: auto;
                    background-color: var(--base-color);
                    --base-color: #523c64;
                }
                .loader {
                    width: 180px;  /* 3 times larger */
                    height: 120px;  /* 3 times larger */
                    position: relative;
                    display: inline-block;
                    background-color: var(--base-color);
                }
                .loader::before {
                    content: '';
                    left: 0;
                    top: 0;
                    position: absolute;
                    width: 108px;  /* 3 times larger */
                    height: 108px;  /* 3 times larger */
                    border-radius: 50%;
                    background-color: #FFF;
                    background-image: radial-gradient(circle 24px at 54px 54px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 54px 0px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 0px 54px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 108px 54px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 54px 108px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 90px 15px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 90px 15px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 90px 90px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 15px 90px, var(--base-color) 100%, transparent 0), radial-gradient(circle 12px at 15px 15px, var(--base-color) 100%, transparent 0);
                    background-repeat: no-repeat;
                    box-sizing: border-box;
                    animation: rotationBack 3s linear infinite;
                }
                .loader::after {
                    content: '';
                    left: 105px;  /* Adjusted for larger size */
                    top: 45px;  /* Adjusted for larger size */
                    position: absolute;
                    width: 72px;  /* 3 times larger */
                    height: 72px;  /* 3 times larger */
                    border-radius: 50%;
                    background-color: #FFF;
                    background-image: radial-gradient(circle 15px at 36px 36px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 36px 0px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 0px 36px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 72px 36px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 36px 72px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 60px 9px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 60px 9px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 60px 60px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 9px 60px, var(--base-color) 100%, transparent 0), radial-gradient(circle 7.5px at 9px 9px, var(--base-color) 100%, transparent 0);
                    background-repeat: no-repeat;
                    box-sizing: border-box;
                    animation: rotationBack 3s linear infinite;
                }
                @keyframes rotationBack {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(-360deg);
                }
                }  
            </style>
            <div class="bg">
                <div class="loader"></div>
            </div>
        """
    )