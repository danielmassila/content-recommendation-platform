// TODO backend: remplacer ces mocks par des appels au service Spring Boot de recommandation.
// L'idée est de garder les pages déjà découplées de la source de données.
export const recommendationApi = {
  async getTonightPick() {
    throw new Error('Endpoint de recommandation non branché')
  },
  async getProfile() {
    throw new Error('Endpoint profil non branché')
  },
  async savePreferences() {
    throw new Error('Endpoint préférences non branché')
  },
}
