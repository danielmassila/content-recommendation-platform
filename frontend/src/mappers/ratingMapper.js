export const getLatestRatingsByItemId = (ratings) => {
  const ratingsByItem = new Map()

  ratings.forEach((rating) => {
    const currentRating = ratingsByItem.get(rating.itemId)
    const currentDate = currentRating ? new Date(currentRating.createdAt).getTime() : 0
    const nextDate = rating.createdAt ? new Date(rating.createdAt).getTime() : 0

    if (!currentRating || nextDate >= currentDate) {
      ratingsByItem.set(rating.itemId, rating)
    }
  })

  return ratingsByItem
}
