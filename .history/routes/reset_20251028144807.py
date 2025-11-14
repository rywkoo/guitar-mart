document.getElementById("verifyToken").addEventListener("click", async () => {
    const token = document.getElementById("token").value.trim();
    tokenGlobal = token;

    if (!token) {
        modalMsg.textContent = "Please enter the token.";
        modalMsg.className = "msg error";
        return;
    }

    // verify token with backend
    try {
        const res = await fetch("/api/reset/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: emailGlobal, token: tokenGlobal }),
        });
        const data = await res.json();

        if (res.ok) {
            // Token valid, show new password form
            modalContent.innerHTML = `
                <h3>Set New Password</h3>
                <input type="password" id="newPassword" placeholder="New Password" required>
                <input type="password" id="confirmPassword" placeholder="Confirm Password" required>
                <button id="submitNewPassword">Reset Password</button>
                <div id="modalMsg" class="msg"></div>
            `;

            document.getElementById("submitNewPassword").addEventListener("click", async () => {
                const newPassword = document.getElementById("newPassword").value.trim();
                const confirmPassword = document.getElementById("confirmPassword").value.trim();
                const modalMsgInner = document.getElementById("modalMsg");

                if (!newPassword || !confirmPassword) {
                    modalMsgInner.textContent = "Please fill both fields.";
                    modalMsgInner.className = "msg error";
                    return;
                }

                if (newPassword !== confirmPassword) {
                    modalMsgInner.textContent = "Passwords do not match.";
                    modalMsgInner.className = "msg error";
                    return;
                }

                try {
                    const res = await fetch("/api/reset/reset", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email: emailGlobal, token: tokenGlobal, new_password: newPassword }),
                    });
                    const data = await res.json();

                    if (res.ok) {
                        modalMsgInner.textContent = data.message || "Password reset successfully!";
                        modalMsgInner.className = "msg success";
                        setTimeout(() => { modal.style.display = "none"; }, 2000);
                    } else {
                        modalMsgInner.textContent = data.error || data.message || "Error resetting password.";
                        modalMsgInner.className = "msg error";
                    }
                } catch {
                    modalMsgInner.textContent = "Network error.";
                    modalMsgInner.className = "msg error";
                }
            });

        } else {
            modalMsg.textContent = data.error || "Invalid token.";
            modalMsg.className = "msg error";
        }
    } catch {
        modalMsg.textContent = "Network error.";
        modalMsg.className = "msg error";
    }
});


reset_bp.route("/request", methods=["POST"])(request_reset)
reset_bp.route("/reset", methods=["POST"])(reset_password)
