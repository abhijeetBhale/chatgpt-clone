import { IKContext, IKUpload } from 'imagekitio-react'
import { useRef, useImperativeHandle, forwardRef, useState, useEffect } from 'react';

const urlEndpoint = import.meta.env.VITE_IMAGEKIT_URL_ENDPOINT;
const publicKey = import.meta.env.VITE_IMAGEKIT_URL_PUBLIC_KEY;

if (!publicKey || !urlEndpoint) {
    console.error("[Upload] Missing ImageKit env vars:", {
        publicKey: publicKey ? "set" : "MISSING",
        urlEndpoint: urlEndpoint ? "set" : "MISSING",
    });
}

const authenticator = async () => {
    try {
        const apiUrl = import.meta.env.VITE_API_URL;
        const response = await fetch(`${apiUrl}/api/upload`);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Request failed with status ${response.status}: ${errorText}`
            );
        }

        const data = await response.json();
        const { signature, expire, token } = data;
        return { signature, expire, token };
    } catch (error) {
        throw new Error(`Authentication request failed: ${error.message}`);
    }
};

const Upload = forwardRef(({ setImg, onUpgradeRequired }, ref) => {

    const ikUploadRef = useRef(null);
    const [uploadConfig, setUploadConfig] = useState(null);
    const rejectedFile = useRef(false);

    // Fetch upload config (plan-based file size limits) on mount
    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL;
                const response = await fetch(`${apiUrl}/api/upload/config`);
                if (response.ok) {
                    const config = await response.json();
                    setUploadConfig(config);
                }
            } catch (err) {
                console.warn("[Upload] Could not fetch upload config:", err);
            }
        };
        fetchConfig();
    }, []);

    const validateFile = (file) => {
        if (!file) return false;

        // Check file type - only images allowed
        if (!file.type.startsWith('image/')) {
            setImg((prev) => ({
                ...prev,
                isLoading: false,
                error: "Only image files are allowed"
            }));
            return false;
        }

        // Check file size against plan limit
        const maxSize = uploadConfig?.maxFileSize || 2 * 1024 * 1024; // Default 2MB
        if (file.size > maxSize) {
            const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
            const maxSizeMB = uploadConfig?.maxFileSizeMB || 2;

            // Always clear any existing image state first
            setImg({ isLoading: false, error: "", dbData: {}, aiData: {} });

            // Free plan exceeded — show upgrade modal
            if (uploadConfig?.plan === 'free' || !uploadConfig?.plan) {
                if (onUpgradeRequired) {
                    onUpgradeRequired({
                        fileSizeMB,
                        maxFileSizeMB: maxSizeMB,
                        currentPlan: uploadConfig?.plan || 'free',
                    });
                }
            } else {
                // Pro plan but still over limit (shouldn't happen, but handle it)
                setImg((prev) => ({
                    ...prev,
                    isLoading: false,
                    error: `File too large (${fileSizeMB}MB). Maximum size is ${maxSizeMB}MB.`
                }));
            }
            return false;
        }

        return true;
    };

    useImperativeHandle(ref, () => ({
        uploadFile: (file) => {
            if (!file) return;
            if (!validateFile(file)) {
                rejectedFile.current = true;
                return;
            }

            rejectedFile.current = false;
            setImg((prev) => ({ ...prev, isLoading: true, error: "" }));
            const reader = new FileReader();
            reader.onload = () => {
                setImg((prev) => ({
                    ...prev,
                    isLoading: true,
                    aiData: {
                        inlineData: {
                            data: reader.result.split(',')[1],
                            mimeType: file.type,
                        }
                    }
                }));
            };
            reader.readAsDataURL(file);

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            const input = ikUploadRef.current?.input;
            if (input) {
                input.files = dataTransfer.files;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }));

    const onError = err => {
        console.error("Upload error:", err);
        setImg((prev) => ({ ...prev, isLoading: false, error: err.message || "Upload failed" }));
    };

    const onSuccess = res => {
        if (rejectedFile.current) {
            rejectedFile.current = false;
            return;
        }
        setImg((prev) => ({ ...prev, isLoading: false, dbData: res }));
    };

    const onUploadProgress = progress => {
        // progress tracking if needed
    };

    const onUploadStart = evt => {
        const file = evt.target.files[0];
        if (!file) return;

        if (!validateFile(file)) {
            rejectedFile.current = true;
            // Reset the file input so the same file can be selected again
            evt.target.value = '';
            return;
        }

        rejectedFile.current = false;
        const reader = new FileReader();
        reader.onload = () => {
            setImg((prev) => ({
                ...prev, isLoading: true, aiData: {
                    inlineData: {
                        data: reader.result.split(',')[1],
                        mimeType: file.type,
                    }
                }
            }));
        };
        reader.readAsDataURL(file);
    }
    return (
        <IKContext
            publicKey={publicKey}
            urlEndpoint={urlEndpoint}
            authenticator={authenticator}
        >
            <IKUpload
                onError={onError}
                onSuccess={onSuccess}
                useUniqueFileName={true}
                onUploadProgress={onUploadProgress}
                onUploadStart={onUploadStart}
                style={{ display: 'none' }}
                ref={ikUploadRef}
            />
            {<label onClick={() => ikUploadRef.current.click()}><img src="/attachment.png" alt="" /></label>}
        </IKContext>
    );
});

Upload.displayName = 'Upload';

export default Upload;
