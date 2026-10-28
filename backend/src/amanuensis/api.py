from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from amanuensis.separation import Separation, SeparationService


def create_app(service: SeparationService) -> FastAPI:
    app = FastAPI(title="Amanuensis")

    @app.post("/separations", status_code=status.HTTP_202_ACCEPTED)
    def create_separation(file: UploadFile, background: BackgroundTasks) -> Separation:
        separation = service.submit(file.filename or "", file.file)
        background.add_task(service.run, separation.id)
        return separation

    @app.get("/separations/{separation_id}")
    def get_separation(separation_id: str) -> Separation:
        separation = service.get(separation_id)
        if separation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown separation")
        return separation

    @app.get("/separations/{separation_id}/stems/{stem}")
    def get_stem(separation_id: str, stem: str) -> FileResponse:
        path = service.stem_path(separation_id, stem)
        if path is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown stem")
        return FileResponse(path, media_type="audio/wav")

    return app
