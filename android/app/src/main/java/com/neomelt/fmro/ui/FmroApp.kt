package com.neomelt.fmro.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import java.util.Locale

@Composable
fun FmroApp(vm: FmroViewModel = viewModel()) {
    val ui by vm.uiState.collectAsStateWithLifecycle()
    var showAddDialog by remember { mutableStateOf(false) }
    val uriHandler = LocalUriHandler.current

    val visibleItems = if (ui.selectedStage == "All") {
        ui.items
    } else {
        ui.items.filter { it.stage == ui.selectedStage }
    }

    val allCities = remember(ui.jobs) {
        listOf("All") + ui.jobs.map { it.location }.distinct().sorted()
    }

    val filteredJobs = remember(ui.jobs, ui.jobKeyword, ui.cityFilter) {
        ui.jobs.filter { job ->
            val hitKeyword = ui.jobKeyword.isBlank() ||
                job.title.contains(ui.jobKeyword, ignoreCase = true) ||
                job.company.contains(ui.jobKeyword, ignoreCase = true) ||
                job.location.contains(ui.jobKeyword, ignoreCase = true)
            val hitCity = ui.cityFilter == "All" || job.location == ui.cityFilter
            hitKeyword && hitCity
        }
    }

    val selectedJob = ui.jobs.firstOrNull { it.id == ui.selectedJobId }

    val darkTheme = when (ui.themeMode) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
    }

    MaterialTheme(colorScheme = if (darkTheme) darkColorScheme() else lightColorScheme()) {
        Scaffold(
            floatingActionButton = {
                if (ui.selectedTab == AppTab.PIPELINE) {
                    FloatingActionButton(onClick = { showAddDialog = true }) {
                        Text("+")
                    }
                }
            },
            bottomBar = {
                BottomNav(ui.selectedTab, vm::selectTab, ui.languageMode)
            }
        ) { innerPadding ->
            when (ui.selectedTab) {
                AppTab.JOBS -> JobsScreen(
                    innerPadding = innerPadding,
                    ui = ui,
                    jobs = filteredJobs,
                    cities = allCities,
                    onRefresh = vm::refresh,
                    onCrawl = vm::crawlAndImportJobs,
                    onKeywordChange = vm::setJobKeyword,
                    onCitySelect = vm::setCityFilter,
                    onSelectJob = vm::selectJob,
                    onOpenUrl = { url -> if (url.isNotBlank()) uriHandler.openUri(url) },
                    onToggleBookmark = vm::toggleBookmark,
                    onApproveReview = vm::approveReview,
                    onRejectReview = vm::rejectReview,
                )

                AppTab.PIPELINE -> PipelineScreen(
                    innerPadding = innerPadding,
                    ui = ui,
                    visibleItems = visibleItems,
                    onRefresh = vm::refresh,
                    onStageSelect = vm::selectStage,
                    onSelectItem = vm::selectItem,
                    onNextStage = vm::moveToNextStage,
                    onReject = vm::markRejected,
                    onOffer = vm::markOffer,
                    onDelete = vm::deleteApplication,
                )

                AppTab.SETTINGS -> SettingsScreen(
                    innerPadding = innerPadding,
                    ui = ui,
                    onThemeMode = vm::setThemeMode,
                    onLanguageMode = vm::setLanguageMode,
                    onAutoUpdate = vm::setAutoUpdate,
                    onBackendBaseUrlInput = vm::setBackendBaseUrlInput,
                    onApplyBackendBaseUrl = vm::applyBackendBaseUrl,
                    onCrawlerImportLimit = vm::setCrawlerImportLimit,
                    onCheckUpdates = vm::checkUpdates,
                    onOpenRelease = { url -> if (url.isNotBlank()) uriHandler.openUri(url) },
                )
            }
        }
    }

    if (showAddDialog) {
        AddApplicationDialog(
            onDismiss = { showAddDialog = false },
            onConfirm = { company, role ->
                vm.addApplication(company, role)
                showAddDialog = false
            }
        )
    }

    if (selectedJob != null && ui.selectedTab == AppTab.JOBS) {
        JobDetailDialog(
            lang = ui.languageMode,
            job = selectedJob,
            bookmarked = ui.bookmarkedJobIds.contains(selectedJob.id),
            onDismiss = { vm.selectJob(null) },
            onApply = { if (selectedJob.applyUrl.isNotBlank()) uriHandler.openUri(selectedJob.applyUrl) },
            onOpenSource = {
                val source = if (selectedJob.sourceUrl.isNotBlank()) selectedJob.sourceUrl else selectedJob.applyUrl
                if (source.isNotBlank()) uriHandler.openUri(source)
            },
            onBookmark = { vm.toggleBookmark(selectedJob.id) },
            onTrack = {
                vm.addApplicationFromJob(selectedJob)
                vm.selectJob(null)
                vm.selectTab(AppTab.PIPELINE)
            },
        )
    }
}

@Composable
private fun BottomNav(
    selectedTab: AppTab,
    onSelect: (AppTab) -> Unit,
    lang: LanguageMode,
) {
    NavigationBar {
        NavigationBarItem(
            selected = selectedTab == AppTab.JOBS,
            onClick = { onSelect(AppTab.JOBS) },
            icon = { Text("📦") },
            label = { Text(i18n(lang, "Jobs", "岗位")) },
        )
        NavigationBarItem(
            selected = selectedTab == AppTab.PIPELINE,
            onClick = { onSelect(AppTab.PIPELINE) },
            icon = { Text("🧭") },
            label = { Text(i18n(lang, "Pipeline", "流程")) },
        )
        NavigationBarItem(
            selected = selectedTab == AppTab.SETTINGS,
            onClick = { onSelect(AppTab.SETTINGS) },
            icon = { Text("⚙️") },
            label = { Text(i18n(lang, "Settings", "设置")) },
        )
    }
}

@Composable
private fun JobsScreen(
    innerPadding: PaddingValues,
    ui: FmroUiState,
    jobs: List<UiJobItem>,
    cities: List<String>,
    onRefresh: () -> Unit,
    onCrawl: () -> Unit,
    onKeywordChange: (String) -> Unit,
    onCitySelect: (String) -> Unit,
    onSelectJob: (Long?) -> Unit,
    onOpenUrl: (String) -> Unit,
    onToggleBookmark: (Long) -> Unit,
    onApproveReview: (Long) -> Unit,
    onRejectReview: (Long) -> Unit,
) {
    val lang = ui.languageMode

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(i18n(lang, "Robot Job Collection", "机器人岗位收集"), style = MaterialTheme.typography.headlineSmall)

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = onRefresh) { Text(i18n(lang, "Refresh", "刷新")) }
            Button(onClick = onCrawl) { Text(i18n(lang, "Crawl Jobs", "抓取岗位")) }
        }

        OutlinedTextField(
            value = ui.jobKeyword,
            onValueChange = onKeywordChange,
            label = { Text(i18n(lang, "Search company/role/city", "搜索公司/岗位/城市")) },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(cities) { city ->
                val selected = ui.cityFilter == city
                val label = if (city == "All") i18n(lang, "All Cities", "全部城市") else city
                if (selected) {
                    Button(onClick = { onCitySelect(city) }) { Text(label) }
                } else {
                    OutlinedButton(onClick = { onCitySelect(city) }) { Text(label) }
                }
            }
        }

        if (ui.loading) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                CircularProgressIndicator(modifier = Modifier.padding(top = 2.dp))
                Text(i18n(lang, "Loading jobs...", "正在加载岗位..."))
            }
        }

        ui.updateStatus?.let { msg ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(msg, modifier = Modifier.padding(10.dp), style = MaterialTheme.typography.bodySmall)
            }
        }

        if (ui.reviewQueue.isNotEmpty()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(i18n(lang, "Pending Review Queue", "待审核抓取"), style = MaterialTheme.typography.titleSmall)
                    ui.reviewQueue.take(3).forEach { review ->
                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text("${review.company} · ${review.title}", style = MaterialTheme.typography.bodyMedium)
                            Text(i18n(lang, "Location", "地点") + ": ${review.location}", style = MaterialTheme.typography.bodySmall)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                if (review.applyUrl.isNotBlank()) {
                                    OutlinedButton(onClick = { onOpenUrl(review.applyUrl) }) {
                                        Text(i18n(lang, "Preview", "预览"))
                                    }
                                }
                                Button(onClick = { onApproveReview(review.id) }) {
                                    Text(i18n(lang, "Approve", "通过"))
                                }
                                OutlinedButton(onClick = { onRejectReview(review.id) }) {
                                    Text(i18n(lang, "Reject", "拒绝"))
                                }
                            }
                        }
                    }
                    if (ui.reviewQueue.size > 3) {
                        Text(
                            i18n(lang, "More pending", "更多待审核") + ": ${ui.reviewQueue.size - 3}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.weight(1f)) {
            if (jobs.isEmpty()) {
                item {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            i18n(lang, "No jobs found with current filters.", "当前筛选下暂无岗位。"),
                            modifier = Modifier.padding(12.dp),
                        )
                    }
                }
            } else {
                items(jobs, key = { it.id }) { job ->
                    val bookmarked = ui.bookmarkedJobIds.contains(job.id)
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectJob(job.id) }
                    ) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(job.title, style = MaterialTheme.typography.titleSmall)
                                Text(if (bookmarked) "★" else "☆")
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text(job.company, style = MaterialTheme.typography.bodyMedium)
                                if (job.sourcePlatform.isNotBlank()) {
                                    Text(
                                        text = platformDisplayName(job.sourcePlatform),
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                                        modifier = Modifier
                                            .background(MaterialTheme.colorScheme.secondaryContainer, RoundedCornerShape(4.dp))
                                            .padding(horizontal = 6.dp, vertical = 2.dp),
                                    )
                                }
                            }
                            Text(i18n(lang, "Location", "地点") + ": ${job.location}", style = MaterialTheme.typography.bodySmall)
                            Text(i18n(lang, "Deadline", "截止") + ": ${job.deadline}", style = MaterialTheme.typography.bodySmall)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                if (job.applyUrl.isNotBlank()) {
                                    Button(onClick = { onOpenUrl(job.applyUrl) }) {
                                        Text(i18n(lang, "Apply", "投递"))
                                    }
                                }
                                OutlinedButton(onClick = { onToggleBookmark(job.id) }) {
                                    Text(if (bookmarked) i18n(lang, "Unsave", "取消收藏") else i18n(lang, "Save", "收藏"))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun JobDetailDialog(
    lang: LanguageMode,
    job: UiJobItem,
    bookmarked: Boolean,
    onDismiss: () -> Unit,
    onApply: () -> Unit,
    onOpenSource: () -> Unit,
    onBookmark: () -> Unit,
    onTrack: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(job.title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(job.company)
                if (job.sourcePlatform.isNotBlank()) {
                    Text(i18n(lang, "Source", "来源") + ": ${platformDisplayName(job.sourcePlatform)}")
                }
                Text(i18n(lang, "Location", "地点") + ": ${job.location}")
                Text(i18n(lang, "Deadline", "截止") + ": ${job.deadline}")
                if (job.applyUrl.isNotBlank()) {
                    Text(i18n(lang, "Apply URL", "投递链接") + ": ${job.applyUrl}")
                }
            }
        },
        confirmButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TextButton(onClick = onTrack) { Text(i18n(lang, "Track", "加入流程")) }
                TextButton(onClick = onBookmark) {
                    Text(if (bookmarked) i18n(lang, "Unsave", "取消收藏") else i18n(lang, "Save", "收藏"))
                }
                TextButton(onClick = onApply) { Text(i18n(lang, "Apply", "投递")) }
            }
        },
        dismissButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TextButton(onClick = onOpenSource) { Text(i18n(lang, "Source", "来源")) }
                TextButton(onClick = onDismiss) { Text(i18n(lang, "Close", "关闭")) }
            }
        }
    )
}

@Composable
private fun PipelineScreen(
    innerPadding: PaddingValues,
    ui: FmroUiState,
    visibleItems: List<UiDashboardItem>,
    onRefresh: () -> Unit,
    onStageSelect: (String) -> Unit,
    onSelectItem: (Long) -> Unit,
    onNextStage: (Long) -> Unit,
    onReject: (Long) -> Unit,
    onOffer: (Long) -> Unit,
    onDelete: (Long) -> Unit,
) {
    val selectedItem = ui.items.firstOrNull { it.id == ui.selectedId }
    val lang = ui.languageMode

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text(i18n(lang, "Interview Pipeline", "面试流程"), style = MaterialTheme.typography.headlineSmall)
                Text(i18n(lang, "Track each stage quickly", "追踪每个阶段"), style = MaterialTheme.typography.bodyMedium)
            }
            OutlinedButton(onClick = onRefresh) {
                Text(i18n(lang, "Refresh", "刷新"))
            }
        }

        if (ui.loading) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                CircularProgressIndicator(modifier = Modifier.padding(top = 2.dp))
                Text(i18n(lang, "Loading applications...", "正在加载投递记录..."))
            }
        }

        if (ui.syncing) {
            Text(i18n(lang, "Syncing changes...", "正在同步变更..."), style = MaterialTheme.typography.labelMedium)
        }

        ui.error?.let { msg ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(msg, modifier = Modifier.padding(10.dp), style = MaterialTheme.typography.bodySmall)
            }
        }

        StatsRow(items = ui.items, lang = lang)
        StageFilters(selectedStage = ui.selectedStage, onStageSelect = onStageSelect, lang = lang)

        LazyColumn(
            modifier = Modifier.weight(1f, fill = true),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            if (visibleItems.isEmpty()) {
                item {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            i18n(lang, "No items in this stage yet.", "该阶段暂无记录。"),
                            modifier = Modifier.padding(12.dp),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                }
            } else {
                items(visibleItems, key = { it.id }) { item ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectItem(item.id) }
                    ) {
                        Column(
                            modifier = Modifier.padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp),
                        ) {
                            Text(item.company, style = MaterialTheme.typography.titleSmall)
                            Text(item.role, style = MaterialTheme.typography.bodyMedium)
                            Text(i18n(lang, "Stage", "阶段") + ": ${item.stage}", style = MaterialTheme.typography.bodySmall)
                            Text(i18n(lang, "Deadline", "截止") + ": ${item.deadline}", style = MaterialTheme.typography.bodySmall)
                            if (ui.selectedId == item.id) {
                                Text(i18n(lang, "Selected", "已选中"), style = MaterialTheme.typography.labelSmall)
                            }
                        }
                    }
                }
            }
        }

        if (selectedItem != null) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(i18n(lang, "Quick Actions", "快捷操作"), style = MaterialTheme.typography.titleSmall)
                    Text("${selectedItem.company} · ${selectedItem.role}")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { onNextStage(selectedItem.id) }) {
                            Text(i18n(lang, "Next Stage", "下一阶段"))
                        }
                        OutlinedButton(onClick = { onReject(selectedItem.id) }) {
                            Text(i18n(lang, "Reject", "拒绝"))
                        }
                        Button(onClick = { onOffer(selectedItem.id) }) {
                            Text(i18n(lang, "Offer", "Offer"))
                        }
                        OutlinedButton(onClick = { onDelete(selectedItem.id) }) {
                            Text(i18n(lang, "Delete", "删除"))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SettingsScreen(
    innerPadding: PaddingValues,
    ui: FmroUiState,
    onThemeMode: (ThemeMode) -> Unit,
    onLanguageMode: (LanguageMode) -> Unit,
    onAutoUpdate: (Boolean) -> Unit,
    onBackendBaseUrlInput: (String) -> Unit,
    onApplyBackendBaseUrl: () -> Unit,
    onCrawlerImportLimit: (Int) -> Unit,
    onCheckUpdates: () -> Unit,
    onOpenRelease: (String) -> Unit,
) {
    val lang = ui.languageMode

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(i18n(lang, "Settings", "设置"), style = MaterialTheme.typography.headlineSmall)

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(i18n(lang, "Theme Mode", "主题模式"), style = MaterialTheme.typography.titleSmall)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    ThemeMode.entries.forEach { mode ->
                        val selected = ui.themeMode == mode
                        if (selected) {
                            Button(onClick = { onThemeMode(mode) }) { Text(themeLabel(mode, lang)) }
                        } else {
                            OutlinedButton(onClick = { onThemeMode(mode) }) { Text(themeLabel(mode, lang)) }
                        }
                    }
                }
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(i18n(lang, "Language", "语言"), style = MaterialTheme.typography.titleSmall)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    LanguageMode.entries.forEach { mode ->
                        val selected = ui.languageMode == mode
                        if (selected) {
                            Button(onClick = { onLanguageMode(mode) }) { Text(langLabel(mode, lang)) }
                        } else {
                            OutlinedButton(onClick = { onLanguageMode(mode) }) { Text(langLabel(mode, lang)) }
                        }
                    }
                }
                Text(
                    i18n(
                        lang,
                        "Language mode currently affects app UI text. Full app locale persistence can be added next.",
                        "当前语言切换已影响应用文案；下个版本可补系统级 Locale 持久化。"
                    ),
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(i18n(lang, "Backend Endpoint", "后端地址"), style = MaterialTheme.typography.titleSmall)
                OutlinedTextField(
                    value = ui.backendBaseUrl,
                    onValueChange = onBackendBaseUrlInput,
                    label = { Text(i18n(lang, "Base URL", "基础 URL")) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = onApplyBackendBaseUrl) {
                        Text(i18n(lang, "Apply Endpoint", "应用地址"))
                    }
                }
                Text(
                    i18n(
                        lang,
                        "Emulator usually uses http://10.0.2.2:8080/ ; physical phone should use your PC LAN IP.",
                        "模拟器通常用 http://10.0.2.2:8080/；真机请填写你电脑的局域网 IP。"
                    ),
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(i18n(lang, "Crawler Import Scale", "抓取导入规模"), style = MaterialTheme.typography.titleSmall)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(50, 100, 200).forEach { limit ->
                        val selected = ui.crawlerImportLimit == limit
                        if (selected) {
                            Button(onClick = { onCrawlerImportLimit(limit) }) { Text(limit.toString()) }
                        } else {
                            OutlinedButton(onClick = { onCrawlerImportLimit(limit) }) { Text(limit.toString()) }
                        }
                    }
                }
                Text(
                    i18n(lang, "Current limit", "当前导入上限") + ": ${ui.crawlerImportLimit}",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Column {
                        Text(i18n(lang, "Auto Update", "自动更新"), style = MaterialTheme.typography.titleSmall)
                        Text(i18n(lang, "Enable update reminder", "开启版本更新提醒"), style = MaterialTheme.typography.bodySmall)
                    }
                    Switch(checked = ui.autoUpdateEnabled, onCheckedChange = onAutoUpdate)
                }

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = onCheckUpdates) {
                        Text(i18n(lang, "Check Update", "检查更新"))
                    }
                    val apkUrl = ui.updateApkUrl
                    if (!apkUrl.isNullOrBlank()) {
                        Button(onClick = { onOpenRelease(apkUrl) }) {
                            Text(i18n(lang, "Update Now", "立即更新"))
                        }
                    }
                    val releaseUrl = ui.releaseUrl
                    if (!releaseUrl.isNullOrBlank()) {
                        OutlinedButton(onClick = { onOpenRelease(releaseUrl) }) {
                            Text(i18n(lang, "Open Release", "打开发布页"))
                        }
                    }
                }

                ui.latestVersion?.let {
                    Text(i18n(lang, "Latest", "最新版本") + ": $it", style = MaterialTheme.typography.bodySmall)
                }
                ui.updateStatus?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun AddApplicationDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, String) -> Unit,
) {
    var company by remember { mutableStateOf("") }
    var role by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Application") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = company,
                    onValueChange = { company = it },
                    label = { Text("Company") },
                    singleLine = true,
                )
                OutlinedTextField(
                    value = role,
                    onValueChange = { role = it },
                    label = { Text("Role") },
                    singleLine = true,
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(company, role) },
                enabled = company.isNotBlank() && role.isNotBlank(),
            ) {
                Text("Add")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@Composable
private fun StatsRow(items: List<UiDashboardItem>, lang: LanguageMode) {
    val offerCount = items.count { it.stage == "Offer" }
    val interviewCount = items.count { it.stage.startsWith("Interview") }
    val pendingCount = items.count { it.stage == "Applied" || it.stage == "OA" }

    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        StatCard(i18n(lang, "Pending", "待推进"), pendingCount, Modifier.weight(1f))
        StatCard(i18n(lang, "Interview", "面试中"), interviewCount, Modifier.weight(1f))
        StatCard(i18n(lang, "Offer", "Offer"), offerCount, Modifier.weight(1f))
    }
}

@Composable
private fun StatCard(label: String, value: Int, modifier: Modifier = Modifier) {
    Card(modifier = modifier) {
        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(label, style = MaterialTheme.typography.labelMedium)
            Text(value.toString(), style = MaterialTheme.typography.titleLarge)
        }
    }
}

@Composable
private fun StageFilters(selectedStage: String, onStageSelect: (String) -> Unit, lang: LanguageMode) {
    val stages = listOf("All") + stageFlow + listOf("Rejected")
    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        items(stages) { stage ->
            val selected = stage == selectedStage
            val label = when (stage) {
                "All" -> i18n(lang, "All", "全部")
                "Rejected" -> i18n(lang, "Rejected", "拒绝")
                else -> stage
            }
            if (selected) {
                Button(onClick = { onStageSelect(stage) }) {
                    Text(label)
                }
            } else {
                OutlinedButton(onClick = { onStageSelect(stage) }) {
                    Text(label)
                }
            }
        }
    }
}

private fun platformDisplayName(code: String): String = when (code) {
    "boss_zhipin" -> "Boss\u76f4\u8058"
    "liepin" -> "\u730e\u8058"
    "shixiseng" -> "\u5b9e\u4e60\u50e7"
    "career_page" -> "\u5b98\u7f51"
    "crawler.website" -> "\u7f51\u9875\u722c\u53d6"
    else -> code
}

private fun i18n(mode: LanguageMode, en: String, zh: String): String {
    val resolved = when (mode) {
        LanguageMode.EN -> "en"
        LanguageMode.ZH -> "zh"
        LanguageMode.SYSTEM -> Locale.getDefault().language
    }
    return if (resolved.startsWith("zh")) zh else en
}

private fun themeLabel(mode: ThemeMode, lang: LanguageMode): String = when (mode) {
    ThemeMode.SYSTEM -> i18n(lang, "System", "跟随系统")
    ThemeMode.LIGHT -> i18n(lang, "Light", "白天")
    ThemeMode.DARK -> i18n(lang, "Dark", "黑夜")
}

private fun langLabel(mode: LanguageMode, lang: LanguageMode): String = when (mode) {
    LanguageMode.SYSTEM -> i18n(lang, "System", "系统")
    LanguageMode.ZH -> "中文"
    LanguageMode.EN -> "English"
}
