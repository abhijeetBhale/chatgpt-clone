import { IKContext, IKUpload } from 'imagekitio-react'
import { useRef } from 'react';

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

const Upload = ({ setImg }) => {

    const ikUploadRef = useRef(null);

    const onError = err => {
        console.error("Upload error:", err);
    };

    const onSuccess = res => {
        setImg((prev) => ({ ...prev, isLoading: false, dbData: res }));
    };

    const onUploadProgress = progress => {
        // progress tracking if needed
    };

    const onUploadStart = evt => {
        const file = evt.target.files[0];

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
}

export default Upload;
