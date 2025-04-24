// src/components/Sidebar.js
import React, { useState, useEffect } from "react"; // Removed useRef
import { uploadDocument, listDocuments, deleteDocument } from "../services/api";
import "./Sidebar.css";


function Sidebar({ isOpen, toggleSidebar, selectedModel, onModelChange, onDocumentsUpdate}) {
    // --- Existing State ---
    const modelOptions = ["gemini-1.5-flash", "gemini-2.0-flash-001"];
    const [documents, setDocuments] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [websiteUrl, setWebsiteUrl] = useState("");
    const [selectedDocToDelete, setSelectedDocToDelete] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [activeTab, setActiveTab] = useState("file");

    const fetchDocs = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const docs = await listDocuments();
            const validDocs = Array.isArray(docs) ? docs : [];
            // update document
            setDocuments(validDocs);

            if (validDocs.length > 0) {
                const currentSelectionValid = validDocs.some(doc => doc.id.toString() === selectedDocToDelete.toString());
                if (!selectedDocToDelete || !currentSelectionValid) {
                    setSelectedDocToDelete(validDocs[0].id);
                }
            } 
            else {
                setSelectedDocToDelete("");
            }
            onDocumentsUpdate(validDocs);
        } 
        catch (err) {
            console.error("Error in fetchDocs:", err);
            setError(`Failed to fetch documents: ${err.message}`);
            setDocuments([]);
            onDocumentsUpdate([]);
        }
        finally {
            setIsLoading(false);
        }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    };
    // the empty dependency array [] means this effect runs only once,
    // right after the Sidebar component mounts for the very first time.
    // Its job is to call fetchDocs() immediately upon mounting to populate 
    // the initial state of the documents list based on what's currently stored on the server.
    useEffect(() => {
      fetchDocs();
    }, []);

  
  const handleFileChange = (event) => {
      setSelectedFile(event.target.files[0]);
      setError(null);
      setSuccessMessage(null);
  };

  const handleUrlChange = (event) => {
      setWebsiteUrl(event.target.value);
      setError(null);
      setSuccessMessage(null);
  };

  const handleFileUpload = async () => {
      if (!selectedFile) {
          setError("Please select a file first.");
          return;
      }
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
      try {
          const response = await uploadDocument(selectedFile);
          setSuccessMessage(
            `File '${selectedFile.name}' uploaded successfully with ID ${response.file_id}.`
          );

          // after succcessfully processed the file, we assign everything to its original state
          setSelectedFile(null);
          // <input type="file"> is largely uncontrolled regarding its value for security reasons. 
          // React state cannot directly set which file is selected. Therefore, after an upload, 
          // the only way to clear the browser's visual representation of the selected file is to directly 
          // manipulate the DOM element's value property using document.getElementById(...)
          const fileInput = document.getElementById("file-upload-input");
          if (fileInput) fileInput.value = "";
          fetchDocs();
      } 
      catch (err) {
          setError(`File upload failed: ${err.message}`);
      } 
      finally {
          setIsLoading(false);
      }
  };

  const handleUrlUpload = async () => {
      if (!websiteUrl || !websiteUrl.trim().startsWith("http")) {
          setError("Please enter a valid website URL (starting with http/https).");
          return;
      }
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
  
      try {
          const response = await uploadDocument({ url: websiteUrl.trim() });
          setSuccessMessage(
            `Website content uploaded successfully with ID ${response.file_id}.`
          );
          // The <input type="text"> element used for the website URL is a controlled component in React.
          setWebsiteUrl("");
          fetchDocs();
      } 
      catch (err) {
          setError(`Website processing failed: ${err.message}`);
      } 
      finally {
          setIsLoading(false);
      }
  };

  const handleDelete = async () => {
      if (!selectedDocToDelete) {
          setError("Please select a document to delete.");
          return;
      }
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
      try {
          await deleteDocument(selectedDocToDelete);
          setSuccessMessage(
            `Document with ID ${selectedDocToDelete} deleted successfully.`
          );
          setSelectedDocToDelete('');
          fetchDocs();
      } 
      catch (err) {
          setError(`Failed to delete document: ${err.message}`);
      } 
      finally {
          setIsLoading(false);
      }
  };



  return (
    <>
      {/* Button to open the sidebar when it's closed */}
      {!isOpen && (
         <button onClick={toggleSidebar} className="sidebar-toggle-button closed" aria-label="Open sidebar">
            {/* SVG Icon */}
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path fillRule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
            </svg>
         </button>
      )}

      {/* The Sidebar itself */}
      <div
        
        className={`sidebar ${isOpen ? "open" : "closed"}`}
        // Removed inline style for width - now controlled purely by CSS
        aria-hidden={!isOpen}
      >
        {/* Only render content when open */}
        {isOpen && (
          <>
            {/* Button to close the sidebar when it's open */}
            <button onClick={toggleSidebar} className="sidebar-toggle-button open" aria-label="Close sidebar">
               {/* SVG Icon */}
               <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path fillRule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
              </svg>
            </button>


            {/* Model Selection */}
            <div className="sidebar-section">
              <h3>Select Model</h3>
              <select
                value={selectedModel}
                onChange={(e) => onModelChange(e.target.value)}
                disabled={isLoading}
              >
                {modelOptions.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            
            {/* Add Document Section */}
            <div className="sidebar-section">
              <h3>Add Document</h3>
              <div className="tabs">
                <button
                  className={activeTab === "file" ? "active" : ""}
                  onClick={() => setActiveTab("file")}
                  disabled={isLoading}
                >
                  File Upload
                </button>
                <button
                  className={activeTab === "url" ? "active" : ""}
                  onClick={() => setActiveTab("url")}
                  disabled={isLoading}
                >
                  Website URL
                </button>
              </div>

              {activeTab === "file" && (
                <div className="tab-content">
                  <input
                    id="file-upload-input"
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileChange}
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleFileUpload}
                    disabled={isLoading || !selectedFile}
                  >
                    {isLoading ? "Uploading..." : "Upload File"}
                  </button>
                </div>
              )}

              {activeTab === "url" && (
                <div className="tab-content">
                  <input
                    type="text"
                    placeholder="https://example.com"
                    value={websiteUrl}
                    onChange={handleUrlChange}
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleUrlUpload}
                    disabled={isLoading || !websiteUrl}
                  >
                    {isLoading ? "Processing..." : "Scrape and Upload"}
                  </button>
                </div>
              )}
              {successMessage && <p className="success-message">{successMessage}</p>}
              {error && <p className="error-message">{error}</p>}
            </div>

            {/* List Documents Section */}
            <div className="sidebar-section">
              <h3>Uploaded Documents</h3>
              <button onClick={fetchDocs} disabled={isLoading}>
                {isLoading && documents.length === 0 ? "Loading..." : "Refresh List"}
              </button>
              <div className="document-list">
                {isLoading && documents.length === 0 && <p className="loading-message">Loading documents...</p>}
                {!isLoading && documents.length === 0 && (
                  <p>No documents uploaded yet.</p>
                )}
                {documents.length > 0 &&
                  documents.map((doc) => (
                    <div key={doc.id} className="document-item">
                      <p title={doc.filename}>
                        <strong>{doc.filename}</strong> ({doc.type === "html" ? "Website" : "Document"})
                      </p>
                      <p className="doc-meta">ID: {doc.id}</p>
                      <p className="doc-meta">
                        Uploaded: {new Date(doc.upload_timestamp).toLocaleString()}
                      </p>
                    </div>
                  ))}
              </div>
            </div>

            {/* Delete Document Section */}
            {documents.length > 0 && (
              <div className="sidebar-section">
                <h3>Delete Document</h3>
                <select
                  value={selectedDocToDelete}
                  onChange={(e) => {
                      setSelectedDocToDelete(e.target.value);
                      setError(null);
                      setSuccessMessage(null);
                  }}
                  disabled={isLoading}
                  aria-label="Select document to delete"
                >
                  <option value="" disabled={!!selectedDocToDelete}>
                    {selectedDocToDelete ? 'Select a document' : '-- Select --'}
                  </option>
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename.length > 30 ? `${doc.filename.substring(0, 27)}...` : doc.filename} (ID: {doc.id})
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleDelete}
                  disabled={isLoading || !selectedDocToDelete}
                >
                  {isLoading ? "Deleting..." : "Delete Selected"}
                </button>
              </div>
            )}
          </>
        )}

       
      </div>
    </>
  );
}

export default Sidebar;