import { ApiError } from "../types/api.ts";
import { useMessagePhoto } from "../hooks/useMessagePhoto.ts";
import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";

export function MessagePhoto({ messageId, hasPhoto }: { messageId: number; hasPhoto: boolean }) {
  const photo = useMessagePhoto(messageId, hasPhoto);

  if (!hasPhoto) {
    return <p className="text-sm text-slate-500">Фото нет</p>;
  }

  if (photo.isLoading) {
    return <div className="h-48 animate-pulse rounded-lg bg-slate-100" aria-label="Загрузка фото" />;
  }

  if (photo.isError) {
    const status = photo.error instanceof ApiError ? photo.error.status : 0;
    const message =
      status === 404 ? "Фото отсутствует" : status === 502 ? getApiErrorMessage(photo.error) : getApiErrorMessage(photo.error);
    return <p className="text-sm text-slate-600">{message}</p>;
  }

  if (!photo.data) {
    return null;
  }

  return (
    <img
      src={photo.data.url}
      alt={`Фото сообщения ${messageId}`}
      className="max-h-[70vh] w-full rounded-lg bg-slate-50 object-contain"
    />
  );
}
