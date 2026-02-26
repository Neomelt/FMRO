package com.neomelt.fmro

import com.neomelt.fmro.model.CreateApplicationRequest
import com.neomelt.fmro.model.CreateCompanyRequest
import com.neomelt.fmro.model.CreateInterviewRoundRequest
import com.neomelt.fmro.model.CreateJobPostingRequest
import com.neomelt.fmro.model.CreateReviewQueueRequest
import com.neomelt.fmro.model.ErrorResponse
import com.neomelt.fmro.model.UpdateApplicationRequest
import com.neomelt.fmro.model.UpdateCompanyRequest
import com.neomelt.fmro.model.UpdateInterviewRoundRequest
import com.neomelt.fmro.model.UpdateJobPostingRequest
import com.neomelt.fmro.store.StoreProvider
import io.ktor.http.HttpStatusCode
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.Application
import io.ktor.server.application.call
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.delete
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.put
import io.ktor.server.routing.route
import io.ktor.server.routing.routing

fun main() {
    embeddedServer(Netty, port = 8080, module = Application::module).start(wait = true)
}

fun Application.module() {
    val store = StoreProvider.store

    install(ContentNegotiation) {
        json()
    }

    routing {
        get("/health") {
            call.respond(mapOf("ok" to true, "service" to "fmro-backend", "store" to store.javaClass.simpleName))
        }

        route("/api/v1") {
            get("/overview") {
                call.respond(store.overview())
            }

            route("/companies") {
                get {
                    call.respond(store.listCompanies())
                }

                post {
                    val req = call.receive<CreateCompanyRequest>()
                    call.respond(HttpStatusCode.Created, store.createCompany(req))
                }

                put("/{id}") {
                    val id = call.pathLong("id") ?: return@put
                    val req = call.receive<UpdateCompanyRequest>()
                    val updated = store.updateCompany(id, req)
                    if (updated == null) {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("company $id not found"))
                    } else {
                        call.respond(updated)
                    }
                }

                delete("/{id}") {
                    val id = call.pathLong("id") ?: return@delete
                    if (store.deleteCompany(id)) {
                        call.respond(HttpStatusCode.NoContent, "")
                    } else {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("company $id not found"))
                    }
                }
            }

            route("/jobs") {
                get {
                    val companyId = call.request.queryParameters["companyId"]?.toLongOrNull()
                    call.respond(store.listJobs(companyId))
                }

                post {
                    val req = call.receive<CreateJobPostingRequest>()
                    val created = runCatching { store.createJob(req) }
                    created.onSuccess {
                        call.respond(HttpStatusCode.Created, it)
                    }.onFailure { e ->
                        call.respond(HttpStatusCode.BadRequest, ErrorResponse(e.message ?: "failed to create job"))
                    }
                }

                put("/{id}") {
                    val id = call.pathLong("id") ?: return@put
                    val req = call.receive<UpdateJobPostingRequest>()
                    val updated = store.updateJob(id, req)
                    if (updated == null) {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("job $id not found"))
                    } else {
                        call.respond(updated)
                    }
                }

                delete("/{id}") {
                    val id = call.pathLong("id") ?: return@delete
                    if (store.deleteJob(id)) {
                        call.respond(HttpStatusCode.NoContent, "")
                    } else {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("job $id not found"))
                    }
                }
            }

            route("/applications") {
                get {
                    val stage = call.request.queryParameters["stage"]
                    call.respond(store.listApplications(stage))
                }

                post {
                    val req = call.receive<CreateApplicationRequest>()
                    val created = runCatching { store.createApplication(req) }
                    created.onSuccess {
                        call.respond(HttpStatusCode.Created, it)
                    }.onFailure { e ->
                        call.respond(HttpStatusCode.BadRequest, ErrorResponse(e.message ?: "failed to create application"))
                    }
                }

                put("/{id}") {
                    val id = call.pathLong("id") ?: return@put
                    val req = call.receive<UpdateApplicationRequest>()
                    val updated = store.updateApplication(id, req)
                    if (updated == null) {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("application $id not found"))
                    } else {
                        call.respond(updated)
                    }
                }

                delete("/{id}") {
                    val id = call.pathLong("id") ?: return@delete
                    if (store.deleteApplication(id)) {
                        call.respond(HttpStatusCode.NoContent, "")
                    } else {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("application $id not found"))
                    }
                }

                get("/{id}/rounds") {
                    val id = call.pathLong("id") ?: return@get
                    call.respond(store.listRounds(id))
                }

                post("/{id}/rounds") {
                    val id = call.pathLong("id") ?: return@post
                    val req = call.receive<CreateInterviewRoundRequest>()
                    val created = runCatching { store.createRound(id, req) }
                    created.onSuccess {
                        call.respond(HttpStatusCode.Created, it)
                    }.onFailure { e ->
                        call.respond(HttpStatusCode.BadRequest, ErrorResponse(e.message ?: "failed to create interview round"))
                    }
                }
            }

            route("/rounds") {
                put("/{id}") {
                    val id = call.pathLong("id") ?: return@put
                    val req = call.receive<UpdateInterviewRoundRequest>()
                    val updated = store.updateRound(id, req)
                    if (updated == null) {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("round $id not found"))
                    } else {
                        call.respond(updated)
                    }
                }

                delete("/{id}") {
                    val id = call.pathLong("id") ?: return@delete
                    if (store.deleteRound(id)) {
                        call.respond(HttpStatusCode.NoContent, "")
                    } else {
                        call.respond(HttpStatusCode.NotFound, ErrorResponse("round $id not found"))
                    }
                }
            }

            route("/review-queue") {
                get {
                    val status = call.request.queryParameters["status"]
                    call.respond(store.listReviewQueue(status))
                }

                post {
                    val req = call.receive<CreateReviewQueueRequest>()
                    call.respond(HttpStatusCode.Created, store.createReview(req))
                }

                post("/{id}/approve") {
                    val id = call.pathLong("id") ?: return@post
                    val created = runCatching { store.approveReview(id) }
                    created.onSuccess {
                        call.respond(HttpStatusCode.Created, it)
                    }.onFailure { e ->
                        val statusCode = if ((e.message ?: "").contains("not found")) {
                            HttpStatusCode.NotFound
                        } else {
                            HttpStatusCode.BadRequest
                        }
                        call.respond(statusCode, ErrorResponse(e.message ?: "failed to approve review"))
                    }
                }

                post("/{id}/reject") {
                    val id = call.pathLong("id") ?: return@post
                    val rejected = runCatching { store.rejectReview(id) }
                    rejected.onSuccess {
                        call.respond(it)
                    }.onFailure { e ->
                        val statusCode = if ((e.message ?: "").contains("not found")) {
                            HttpStatusCode.NotFound
                        } else {
                            HttpStatusCode.BadRequest
                        }
                        call.respond(statusCode, ErrorResponse(e.message ?: "failed to reject review"))
                    }
                }
            }

            route("/crawler") {
                post("/run") {
                    call.respond(store.runCrawler())
                }
            }
        }
    }
}

private suspend fun io.ktor.server.application.ApplicationCall.pathLong(name: String): Long? {
    val value = parameters[name]?.toLongOrNull()
    if (value == null) {
        respond(HttpStatusCode.BadRequest, ErrorResponse("invalid path parameter: $name"))
    }
    return value
}
