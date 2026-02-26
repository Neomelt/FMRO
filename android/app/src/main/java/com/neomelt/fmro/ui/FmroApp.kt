package com.neomelt.fmro.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class DashboardItem(
    val company: String,
    val role: String,
    val stage: String,
    val deadline: String,
)

private val sampleItems = listOf(
    DashboardItem("DJI", "Robotics Intern", "Applied", "2026-03-31"),
    DashboardItem("Unitree", "Perception Intern", "Interview #1", "2026-03-05"),
    DashboardItem("AgiBot", "SLAM Intern", "OA", "2026-03-10"),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FmroApp() {
    MaterialTheme {
        Scaffold(
            topBar = {
                TopAppBar(
                    colors = TopAppBarDefaults.topAppBarColors(),
                    title = { Text("FMRO") },
                )
            }
        ) { innerPadding ->
            DashboardScreen(innerPadding)
        }
    }
}

@Composable
private fun DashboardScreen(innerPadding: PaddingValues) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Find Much Robot Offer", style = MaterialTheme.typography.titleMedium)
        Text("Personal robotics internship tracker", style = MaterialTheme.typography.bodyMedium)

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(sampleItems) { item ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(item.company, style = MaterialTheme.typography.titleSmall)
                        Text(item.role, style = MaterialTheme.typography.bodyMedium)
                        Text("Stage: ${item.stage}", style = MaterialTheme.typography.bodySmall)
                        Text("Deadline: ${item.deadline}", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}
