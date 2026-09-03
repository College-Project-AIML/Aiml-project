const APPLICATIONS_KEY = 'suvidha-applications'

function readAll() {
  try {
    return JSON.parse(localStorage.getItem(APPLICATIONS_KEY)) || []
  } catch {
    return []
  }
}

function saveAll(applications) {
  localStorage.setItem(APPLICATIONS_KEY, JSON.stringify(applications))
}

export function getApplications(userKey) {
  return readAll().filter((application) => application.userKey === userKey)
}

export function trackApplication(userKey, scheme) {
  const applications = readAll()
  const existing = applications.find((application) => application.userKey === userKey && application.scheme.id === scheme.id)
  if (existing) return existing

  const application = {
    id: `${userKey}-${scheme.id}`,
    userKey,
    progress: 'INTERESTED',
    trackedAt: new Date().toISOString(),
    scheme: {
      id: scheme.id,
      name: scheme.name,
      status: scheme.status,
      link: scheme.link,
      state_code: scheme.state_code,
      category_name: scheme.category_name,
      documents_required: scheme.documents_required || [],
      application_deadline: scheme.application_deadline || null,
    },
  }
  applications.push(application)
  saveAll(applications)
  return application
}

export function updateApplicationProgress(applicationId, progress) {
  const applications = readAll().map((application) => (
    application.id === applicationId ? { ...application, progress } : application
  ))
  saveAll(applications)
  return applications
}

export function removeApplication(applicationId) {
  const applications = readAll().filter((application) => application.id !== applicationId)
  saveAll(applications)
  return applications
}
