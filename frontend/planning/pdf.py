"""Display existing backend PDF bytes; no browser document generation or token."""

import reflex as rx


class ApprovedPDFViewer(rx.Component):
    tag = "ApprovedPDFViewer"
    lib_dependencies = ["react-pdf@10.2.0"]
    data: rx.Var[str]
    filename: rx.Var[str]

    def add_imports(self):
        return {
            "react": ["useEffect", "useState", "useMemo", "useRef"],
        }

    def _get_custom_code(self):
        return """
import "react-pdf/dist/Page/TextLayer.css";

function ApprovedPDFViewer({data, filename}) {
    const [pdfLibrary, setPdfLibrary] = useState(null);
    const [url, setUrl] = useState("");
    const [pages, setPages] = useState(0);
    const [page, setPage] = useState(1);
    const [width, setWidth] = useState(300);
    const [zoom, setZoom] = useState(1);
    const [error, setError] = useState(false);
    const container = useRef(null);
    const file = useMemo(() => ({data: Uint8Array.from(
        atob(data.split(",")[1]), c => c.charCodeAt(0)
    )}), [data]);
    useEffect(() => {
        let active = true;
        import("react-pdf").then(library => {
            library.pdfjs.GlobalWorkerOptions.workerSrc = new URL(
                "pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url
            ).toString();
            if (active) setPdfLibrary(library);
        }).catch(() => {if (active) setError(true);});
        return () => {active = false;};
    }, []);
    useEffect(() => {
        if (!data) return;
        const bytes = Uint8Array.from(atob(data.split(",")[1]), c => c.charCodeAt(0));
        const next = URL.createObjectURL(new Blob([bytes], {type: "application/pdf"}));
        setUrl(next);
        return () => URL.revokeObjectURL(next);
    }, [data]);
    useEffect(() => {
        const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
        observer.observe(container.current);
        return () => observer.disconnect();
    }, []);
    const Document = pdfLibrary?.Document;
    const Page = pdfLibrary?.Page;
    const control = {padding: "0.5rem 0.75rem", color: "#173e3d",
        background: "#fff", border: "1px solid #c9d8d1", borderRadius: "6px",
        minHeight: "44px", font: "inherit"};
    return <div ref={container} style={{width: "100%", minWidth: 0}}>
        <p><a href={url} download={filename} style={{display: "inline-block",
            padding: "0.5rem 0.75rem", color: "#173e3d", border: "1px solid #c9d8d1",
            borderRadius: "6px"}}>Download approved PDF</a></p>
        <div style={{display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center",
            marginBottom: "0.75rem"}}>
        <button type="button" style={control} disabled={page <= 1 || error || !pages}
            onClick={() => setPage(current => current - 1)}>Previous PDF page</button>
        <span role="status" aria-live="polite">
            {error ? "PDF preview unavailable" : pages ? `Page ${page} of ${pages}`
                : "Loading PDF pages…"}</span>
        <button type="button" style={control} disabled={page >= pages || error || !pages}
            onClick={() => setPage(current => current + 1)}>Next PDF page</button>
        <label>PDF zoom <select aria-label="PDF zoom" value={zoom} style={control}
            onChange={event => setZoom(Number(event.target.value))}>
            <option value="1">Fit width</option><option value="1.5">150%</option>
            <option value="2">200%</option><option value="3">300%</option>
        </select></label></div>
        {error && <p role="alert">PDF preview unavailable. Approval remains saved.
            Download the PDF or explicitly retry View approved PDF.</p>}
        <div role="region" tabIndex={0} aria-label="Approved procurement PDF"
             style={{maxHeight: "min(700px, 70dvh)", overflow: "auto",
                 border: "1px solid #c9d8d1"}}>
            {pdfLibrary ? <Document file={file} onLoadSuccess={({numPages}) => {
                          setPages(numPages); setPage(1); setError(false);
                      }}
                      onLoadError={() => setError(true)} onSourceError={() => setError(true)}>
                {pages > 0 && <Page key={page} pageNumber={page}
                          width={Math.max(160, width - 4) * zoom}
                          renderAnnotationLayer={false} onRenderError={() => setError(true)} />}
            </Document> : <p role="status">Loading PDF viewer...</p>}
        </div>
    </div>;
}
"""
