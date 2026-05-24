/**
 * Validation form realtime bằng Alpine.js — không dùng HTML5 browser validation.
 * Hiển thị lỗi inline, trạng thái error/success rõ ràng.
 */
document.addEventListener('alpine:init', () => {
    const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const USERNAME_REGEX = /^[a-zA-Z0-9_]+$/;
    const ALLOWED_IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];
    const MAX_AVATAR_MB = 5;

    /** Chuẩn hóa giá trị input — tránh lỗi khi field chưa có trong DOM hoặc value null. */
    const asString = (v) => (v == null ? '' : String(v));

    /** Parse số — hỗ trợ dấu phẩy thập phân (vi-VN). */
    const parseNumber = (v) => {
        const s = asString(v).trim().replace(',', '.');
        if (!s) return NaN;
        return Number(s);
    };

    const RULES = {
        register: {
            username: (v) => {
                const s = asString(v).trim();
                if (!s) return 'Vui lòng nhập tên đăng nhập.';
                if (s.length < 3) return 'Tên đăng nhập phải có ít nhất 3 ký tự.';
                if (!USERNAME_REGEX.test(s)) return 'Tên đăng nhập chỉ được dùng chữ, số và dấu gạch dưới.';
                return '';
            },
            email: (v) => {
                const s = asString(v).trim();
                if (!s) return 'Vui lòng nhập email.';
                if (!EMAIL_REGEX.test(s)) return 'Email không hợp lệ.';
                return '';
            },
            full_name: () => '',
            password: (v) => {
                const s = asString(v);
                if (!s) return 'Vui lòng nhập mật khẩu.';
                if (s.length < 6) return 'Mật khẩu phải có ít nhất 6 ký tự.';
                return '';
            },
            password_confirm: (v, all) => {
                const s = asString(v);
                if (!s) return 'Vui lòng xác nhận mật khẩu.';
                if (s !== asString(all.password)) return 'Mật khẩu xác nhận không khớp.';
                return '';
            },
        },
        login: {
            username: (v) => (!asString(v).trim() ? 'Vui lòng nhập tên đăng nhập hoặc email.' : ''),
            password: (v) => (!asString(v) ? 'Vui lòng nhập mật khẩu.' : ''),
        },
        profile: {
            full_name: () => '',
            email: (v) => {
                const s = asString(v).trim();
                if (!s) return 'Vui lòng nhập email.';
                if (!EMAIL_REGEX.test(s)) return 'Email không hợp lệ.';
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
                const s = asString(v).trim();
                if (!s) return 'Vui lòng nhập tên bộ dữ liệu.';
                if (s.length < 3) return 'Tên bộ dữ liệu phải có ít nhất 3 ký tự.';
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
        training_config: {
            model_name: (v) => {
                const s = asString(v).trim();
                if (!s) return 'Vui lòng nhập tên mô hình.';
                if (s.length < 3) return 'Tên mô hình phải có ít nhất 3 ký tự.';
                return '';
            },
            dataset_id: (v) => (!asString(v).trim() ? 'Vui lòng chọn bộ dữ liệu.' : ''),
            description: () => '',
            epochs: (v) => {
                const s = asString(v).trim();
                const n = parseNumber(s);
                if (!s || Number.isNaN(n)) return 'Vui lòng nhập số epoch.';
                if (n < 1 || n > 100) return 'Số epoch phải từ 1 đến 100.';
                return '';
            },
            batch_size: (v) => {
                const s = asString(v).trim();
                const n = parseNumber(s);
                if (!s || Number.isNaN(n)) return 'Vui lòng nhập batch size.';
                if (n < 4 || n > 128) return 'Batch size phải từ 4 đến 128.';
                return '';
            },
            input_width: (v) => {
                const s = asString(v).trim();
                const n = parseNumber(s);
                if (!s || Number.isNaN(n)) return 'Vui lòng nhập chiều rộng.';
                if (n < 32 || n > 512) return 'Chiều rộng phải từ 32 đến 512 px.';
                return '';
            },
            input_height: (v) => {
                const s = asString(v).trim();
                const n = parseNumber(s);
                if (!s || Number.isNaN(n)) return 'Vui lòng nhập chiều cao.';
                if (n < 32 || n > 512) return 'Chiều cao phải từ 32 đến 512 px.';
                return '';
            },
            learning_rate: (v) => {
                const s = asString(v).trim();
                const n = parseNumber(s);
                if (!s || Number.isNaN(n)) return 'Vui lòng nhập learning rate.';
                if (n <= 0 || n > 1) return 'Learning rate phải lớn hơn 0 và nhỏ hơn 1.';
                return '';
            },
            optimizer: () => '',
            loss_function: () => '',
        },
    };

    Alpine.data('auroraForm', (formType) => ({
        formType,
        errors: {},
        touched: {},
        success: {},
        submitted: false,
        dragOver: false,
        fileName: '',
        uploading: false,

        init() {
            let serverErrorsJson = '{}';
            const errorsId = this.$el.dataset.errorsId;
            if (errorsId) {
                const node = document.getElementById(errorsId);
                if (node && node.textContent) {
                    serverErrorsJson = node.textContent;
                }
            }
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
            const root = this.$el.querySelector('form') || this.$el;
            root.querySelectorAll('[data-field]').forEach((el) => {
                const name = el.dataset.field;
                if (!name) return;
                if (el.type === 'file') {
                    values[name] = el.files[0] || null;
                } else if (el.type === 'checkbox') {
                    values[name] = el.checked;
                } else {
                    values[name] = el.value ?? '';
                }
            });
            return values;
        },

        getFieldValue(name) {
            const root = this.$el.querySelector('form') || this.$el;
            const el = root.querySelector(`[data-field="${name}"]`);
            if (!el) return '';
            if (el.type === 'file') return el.files[0] || null;
            if (el.type === 'checkbox') return el.checked;
            return el.value ?? '';
        },

        validateField(name) {
            const rules = RULES[this.formType];
            if (!rules || !rules[name]) return;

            const values = this.getValues();
            const value = values[name] !== undefined ? values[name] : this.getFieldValue(name);

            let error = '';
            try {
                error = rules[name](value, values) || '';
            } catch (e) {
                error = 'Giá trị không hợp lệ.';
            }

            if (error) {
                this.errors[name] = error;
                delete this.success[name];
            } else if (this.touched[name] || this.submitted) {
                delete this.errors[name];
                if (name !== 'remember_me' && name !== 'full_name' && name !== 'description') {
                    this.success[name] = true;
                }
            }
        },

        onInput(name) {
            this.touched[name] = true;
            if (name === 'learning_rate') {
                this._normalizeLearningRateInput();
            }
            this.validateField(name);
            if (name === 'password') this.validateField('password_confirm');
        },

        onBlur(name) {
            this.touched[name] = true;
            if (name === 'learning_rate') {
                this._normalizeLearningRateInput();
            }
            this.validateField(name);
        },

        _normalizeLearningRateInput() {
            const el = (this.$el.querySelector('form') || this.$el).querySelector('[data-field="learning_rate"]');
            if (!el) return;
            const normalized = asString(el.value).trim().replace(',', '.');
            if (normalized !== el.value) {
                el.value = normalized;
            }
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
            this.handleFormSubmit(event);
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

        hasErrors() {
            return Object.keys(this.errors).length > 0;
        },

        handleFormSubmit(event) {
            if (!this.validateAll()) {
                event.preventDefault();
                this.$nextTick(() => {
                    const firstError = this.$el.querySelector('.field-error, .field-error-msg');
                    if (firstError) {
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    if (window.lucide) lucide.createIcons();
                });
                return;
            }
            if (this.formType === 'dataset_upload') {
                this.uploading = true;
            }
            /* Hợp lệ — để form submit tự nhiên */
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
