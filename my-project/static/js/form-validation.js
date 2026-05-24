/**
 * Validation form realtime bằng Alpine.js — không dùng HTML5 browser validation.
 * Hiển thị lỗi inline, trạng thái error/success rõ ràng.
 */
document.addEventListener('alpine:init', () => {
    const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const USERNAME_REGEX = /^[a-zA-Z0-9_]+$/;
    const ALLOWED_IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];
    const MAX_AVATAR_MB = 5;

    const RULES = {
        register: {
            username: (v) => {
                if (!v.trim()) return 'Vui lòng nhập tên đăng nhập.';
                if (v.trim().length < 3) return 'Tên đăng nhập phải có ít nhất 3 ký tự.';
                if (!USERNAME_REGEX.test(v.trim())) return 'Tên đăng nhập chỉ được dùng chữ, số và dấu gạch dưới.';
                return '';
            },
            email: (v) => {
                if (!v.trim()) return 'Vui lòng nhập email.';
                if (!EMAIL_REGEX.test(v.trim())) return 'Email không hợp lệ.';
                return '';
            },
            full_name: () => '',
            password: (v) => {
                if (!v) return 'Vui lòng nhập mật khẩu.';
                if (v.length < 6) return 'Mật khẩu phải có ít nhất 6 ký tự.';
                return '';
            },
            password_confirm: (v, all) => {
                if (!v) return 'Vui lòng xác nhận mật khẩu.';
                if (v !== all.password) return 'Mật khẩu xác nhận không khớp.';
                return '';
            },
        },
        login: {
            username: (v) => (!v.trim() ? 'Vui lòng nhập tên đăng nhập hoặc email.' : ''),
            password: (v) => (!v ? 'Vui lòng nhập mật khẩu.' : ''),
        },
        profile: {
            full_name: () => '',
            email: (v) => {
                if (!v.trim()) return 'Vui lòng nhập email.';
                if (!EMAIL_REGEX.test(v.trim())) return 'Email không hợp lệ.';
                return '';
            },
            avatar: (file) => {
                if (!file) return '';
                const name = file.name.toLowerCase();
                const ext = name.slice(name.lastIndexOf('.'));
                if (!ALLOWED_IMAGE_EXT.includes(ext)) {
                    return 'Chỉ chấp nhận ảnh JPG, PNG, WEBP, GIF.';
                }
                if (file.size > MAX_AVATAR_MB * 1024 * 1024) {
                    return `Ảnh không được vượt quá ${MAX_AVATAR_MB}MB.`;
                }
                return '';
            },
        },
        dataset_upload: {
            dataset_name: (v) => {
                if (!v.trim()) return 'Vui lòng nhập tên bộ dữ liệu.';
                if (v.trim().length < 3) return 'Tên bộ dữ liệu phải có ít nhất 3 ký tự.';
                return '';
            },
            description: () => '',
            zip_file: (file, all, maxMb = 500) => {
                if (!file) return 'Vui lòng chọn file ZIP.';
                if (!file.name.toLowerCase().endsWith('.zip')) return 'Chỉ chấp nhận file ZIP.';
                const limit = (window.DATASET_MAX_ZIP_MB || maxMb) * 1024 * 1024;
                if (file.size > limit) {
                    return `File ZIP không được vượt quá ${window.DATASET_MAX_ZIP_MB || maxMb}MB.`;
                }
                return '';
            },
        },
    };

    Alpine.data('auroraForm', (formType, serverErrorsJson = '{}') => ({
        formType,
        errors: {},
        touched: {},
        success: {},
        submitted: false,
        dragOver: false,
        fileName: '',
        uploading: false,

        init() {
            try {
                const serverErrors = JSON.parse(serverErrorsJson || '{}');
                Object.keys(serverErrors).forEach((key) => {
                    const msgs = serverErrors[key];
                    if (msgs && msgs.length) {
                        const first = msgs[0];
                        this.errors[key] = typeof first === 'string' ? first : (first.message || '');
                        this.touched[key] = true;
                    }
                });
            } catch (e) {
                /* Bỏ qua nếu JSON server lỗi */
            }
            this.$nextTick(() => {
                if (window.lucide) lucide.createIcons();
            });
        },

        getValues() {
            const values = {};
            this.$el.querySelectorAll('[data-field]').forEach((el) => {
                const name = el.dataset.field;
                if (el.type === 'file') {
                    values[name] = el.files[0] || null;
                } else if (el.type === 'checkbox') {
                    values[name] = el.checked;
                } else {
                    values[name] = el.value;
                }
            });
            return values;
        },

        validateField(name) {
            const rules = RULES[this.formType];
            if (!rules || !rules[name]) return;

            const values = this.getValues();
            const value = values[name];
            const error = rules[name](value, values);

            if (error) {
                this.errors[name] = error;
                delete this.success[name];
            } else if (this.touched[name] || this.submitted) {
                delete this.errors[name];
                if (name !== 'remember_me' && name !== 'full_name') {
                    this.success[name] = true;
                }
            }
        },

        onInput(name) {
            this.touched[name] = true;
            this.validateField(name);
            if (name === 'password') this.validateField('password_confirm');
        },

        onBlur(name) {
            this.touched[name] = true;
            this.validateField(name);
        },

        onFileChange(name, event) {
            this.touched[name] = true;
            const rules = RULES[this.formType];
            if (!rules || !rules[name]) return;
            const file = event.target.files[0] || null;
            if (file) this.fileName = file.name;
            const error = rules[name](file);
            if (error) {
                this.errors[name] = error;
                delete this.success[name];
            } else if (file) {
                delete this.errors[name];
                this.success[name] = true;
            } else {
                delete this.errors[name];
                delete this.success[name];
                this.fileName = '';
            }
        },

        handleDrop(event) {
            this.dragOver = false;
            const file = event.dataTransfer.files[0];
            if (!file || !this.$refs.zipInput) return;
            const dt = new DataTransfer();
            dt.items.add(file);
            this.$refs.zipInput.files = dt.files;
            this.onFileChange('zip_file', { target: this.$refs.zipInput });
        },

        uploadZoneClass() {
            if (this.showError('zip_file')) return 'upload-zone upload-zone-error';
            if (this.success['zip_file']) return 'upload-zone upload-zone-success';
            if (this.dragOver) return 'upload-zone upload-zone-drag';
            return 'upload-zone';
        },

        onSubmitForm(event) {
            if (!this.validateAll()) {
                event.preventDefault();
                return;
            }
            this.uploading = true;
        },

        validateAll() {
            this.submitted = true;
            const rules = RULES[this.formType];
            if (!rules) return true;

            let valid = true;
            Object.keys(rules).forEach((name) => {
                this.touched[name] = true;
                this.validateField(name);
                if (this.errors[name]) valid = false;
            });
            return valid;
        },

        fieldClass(name) {
            if (this.errors[name] && (this.touched[name] || this.submitted)) {
                return 'aurora-input field-error';
            }
            if (this.success[name]) return 'aurora-input field-success';
            return 'aurora-input';
        },

        fileClass(name) {
            if (this.errors[name] && (this.touched[name] || this.submitted)) {
                return 'aurora-file field-error';
            }
            if (this.success[name]) return 'aurora-file field-success';
            return 'aurora-file';
        },

        showError(name) {
            return (this.touched[name] || this.submitted) && this.errors[name];
        },

        togglePassword(event) {
            const wrapper = event.currentTarget.closest('.password-field');
            const input = wrapper.querySelector('input');
            const icon = wrapper.querySelector('[data-toggle-icon]');
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            icon.setAttribute('data-lucide', isHidden ? 'eye-off' : 'eye');
            if (window.lucide) lucide.createIcons();
        },
    }));
});
