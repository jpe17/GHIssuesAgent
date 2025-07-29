// === APP STATE & MAIN OBJECT ===
const App = {
    state: {
        currentRepoUrl: '',
        issues: [],
        selectedIssues: new Set(),
        currentIssueId: null
    },

    // === MAIN API FUNCTIONS ===
    async fetchIssues() {
        const repoUrl = document.getElementById('repoUrl').value.trim();
        console.log('🔍 Fetch Issues clicked, repo URL:', repoUrl);
        
        if (!repoUrl) {
            this.showMessage('Please enter a repository URL', 'error');
            return;
        }

        this.state.currentRepoUrl = repoUrl;
        const btn = document.querySelector('.btn-primary');
        
        console.log('📤 Setting loading state and showing issues section');
        this.setLoading(btn, 'Fetching Issues...');
        this.showSection('issuesSection');
        this.setIssuesLoading();

        try {
            console.log('🌐 Making API request to /api/fetch-issues');
            const response = await fetch('/api/fetch-issues', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: repoUrl })
            });

            console.log('📥 API response status:', response.status);
            if (!response.ok) throw new Error('Failed to fetch issues');

            const data = await response.json();
            console.log('📊 Received data:', data);
            this.state.issues = data.issues;
            this.renderIssues();
        } catch (error) {
            console.error('❌ Error fetching issues:', error);
            this.showMessage('Failed to fetch issues: ' + error.message, 'error');
            this.hideSection('issuesSection');
        } finally {
            this.clearLoading(btn, '<span>🔍</span> Fetch Issues');
        }
    },

    async analyzeSingle(issueId) {
        const btn = document.getElementById(`play-${issueId}`);
        const row = btn.closest('.issue-item');
        
        this.setLoading(btn, 'Analyzing...');
        row.classList.add('analyzing');
        
        this.showSection('analysisSection');
        this.showElement('analysisLoading');
        this.hideElement('analysisGrid');
        this.hideElement('executeBtn');
        
        document.querySelector('#analysisLoading span').textContent = 
            `Analyzing Issue #${issueId} with AI agents (Agent 2 & 3 running in parallel)...`;

        try {
            const response = await fetch('/api/analyze-issue', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: this.state.currentRepoUrl, issue_id: issueId })
            });

            if (!response.ok) throw new Error('Failed to analyze issue');

            const data = await response.json();
            this.state.currentIssueId = issueId;
            this.renderSingleAnalysis(data.analysis, data.plan, issueId);
        } catch (error) {
            this.showMessage('Failed to analyze issue: ' + error.message, 'error');
            this.hideSection('analysisSection');
        } finally {
            this.clearLoading(btn, 'Analyze');
            row.classList.remove('analyzing');
        }
    },

    async analyzeMultiple() {
        if (this.state.selectedIssues.size === 0) {
            this.showMessage('Please select at least one issue', 'error');
            return;
        }

        const btn = document.getElementById('analyzeAllBtn');
        this.setLoading(btn, 'Analyzing...');
        
        // Update all selected rows
        this.state.selectedIssues.forEach(issueId => {
            const row = document.getElementById(`checkbox-${issueId}`).closest('.issue-item');
            const playBtn = document.getElementById(`play-${issueId}`);
            row.classList.add('analyzing');
            this.setLoading(playBtn, 'Analyzing...');
        });

        this.showSection('multipleAnalysisSection');
        this.showElement('multipleAnalysisLoading');
        this.hideElement('multipleAnalysisGrid');
        
        document.querySelector('#multipleAnalysisLoading span').textContent = 
            `Analyzing ${this.state.selectedIssues.size} issues with AI agents...`;

        try {
            const response = await fetch('/api/analyze-multiple-issues', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    repo_url: this.state.currentRepoUrl, 
                    issue_ids: Array.from(this.state.selectedIssues) 
                })
            });

            if (!response.ok) throw new Error('Failed to analyze issues');

            const data = await response.json();
            this.hideElement('multipleAnalysisLoading');
            this.showElement('multipleAnalysisGrid');
            this.renderMultipleAnalysis(data.results);
        } catch (error) {
            this.showMessage('Failed to analyze issues: ' + error.message, 'error');
            this.hideElement('multipleAnalysisLoading');
        } finally {
            this.clearLoading(btn, '<span>🔍</span> Analyze Selected');
            
            // Restore all rows
            this.state.selectedIssues.forEach(issueId => {
                const row = document.getElementById(`checkbox-${issueId}`).closest('.issue-item');
                const playBtn = document.getElementById(`play-${issueId}`);
                row.classList.remove('analyzing');
                this.clearLoading(playBtn, 'Analyze');
            });
        }
    },

    async execute() {
        if (!this.state.currentIssueId) {
            this.showMessage('No issue selected for execution', 'error');
            return;
        }

        // Show execution section with coffee message
        document.getElementById('executionSection').style.display = 'block';
        document.getElementById('executionLoading').style.display = 'block';
        document.getElementById('executionResult').style.display = 'none';
        
        // Scroll to execution section
        document.getElementById('executionSection').scrollIntoView({ behavior: 'smooth' });

        const btn = document.getElementById('executeBtn');
        this.setLoading(btn, 'Executing...');

        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    repo_url: this.state.currentRepoUrl, 
                    issue_id: this.state.currentIssueId 
                })
            });

            if (!response.ok) throw new Error('Failed to execute changes');

            const data = await response.json();
            
            // Hide loading and show results
            document.getElementById('executionLoading').style.display = 'none';
            document.getElementById('executionResult').style.display = 'block';
            
            if (data.status === 'completed') {
                let message = `<div style="text-align: center;">
                    <h3 style="color: #28a745; margin-bottom: 16px;">🎉 Execution Completed!</h3>
                    <p style="margin-bottom: 16px;">Issue #${this.state.currentIssueId} has been successfully implemented.</p>`;
                
                if (data.pr_url) {
                    message += `<a href="${data.pr_url}" target="_blank" class="btn btn-primary" style="margin-top: 16px;">
                        <span>🔗</span> View Pull Request
                    </a>`;
                } else {
                    message += '<p style="color: #6c757d;">Check the Devin frontend for detailed results.</p>';
                }
                message += '</div>';
                
                document.getElementById('executionResult').innerHTML = message;
                btn.innerHTML = '✅ Completed';
            } else {
                throw new Error('Execution failed');
            }
        } catch (error) {
            // Hide loading and show error
            document.getElementById('executionLoading').style.display = 'none';
            document.getElementById('executionResult').style.display = 'block';
            document.getElementById('executionResult').innerHTML = `
                <div style="text-align: center;">
                    <h3 style="color: #dc3545; margin-bottom: 16px;">❌ Execution Failed</h3>
                    <p>${error.message}</p>
                </div>`;
            btn.innerHTML = '❌ Failed';
        } finally {
            btn.disabled = false;
        }
    },

    async executeSingle(issueId) {
        const btn = document.querySelector(`[onclick="executeSingleIssue('${issueId}')"]`);
        this.setLoading(btn, 'Executing...');

        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    repo_url: this.state.currentRepoUrl, 
                    issue_id: issueId 
                })
            });

            if (!response.ok) throw new Error('Failed to execute changes');

            const data = await response.json();
            if (data.status === 'completed') {
                btn.innerHTML = '✅ Completed';
                let message = `Execution completed for issue #${issueId}!`;
                if (data.pr_url) {
                    message += ` <a href="${data.pr_url}" target="_blank" style="color: #0066cc; text-decoration: underline;">View Pull Request</a>`;
                } else {
                    message += ' Check the Devin frontend for results.';
                }
                this.showMessage(message, 'success');
            } else {
                throw new Error('Execution failed');
            }
        } catch (error) {
            this.showMessage(`Failed to execute issue #${issueId}: ${error.message}`, 'error');
            btn.innerHTML = '❌ Failed';
        } finally {
            btn.disabled = false;
        }
    },

    // === RENDER FUNCTIONS ===
    renderIssues() {
        const container = document.getElementById('issuesList');
        console.log('🎨 Rendering issues, count:', this.state.issues.length);
        
        if (this.state.issues.length === 0) {
            console.log('📭 No issues found, showing empty state');
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                    <h3>No issues found</h3>
                    <p>This repository has no open issues at the moment.</p>
                </div>
            `;
            return;
        }

        console.log('📝 Rendering', this.state.issues.length, 'issues');
        container.innerHTML = this.state.issues.map(issue => `
            <div class="issue-item">
                <div class="issue-info">
                    <div class="issue-header">
                        <span class="issue-number">#${issue.id}</span>
                        <span class="issue-state ${issue.state}">${issue.state}</span>
                    </div>
                    <div class="issue-title">${issue.title}</div>
                    <div class="issue-body">${issue.body || 'No description available'}</div>
                </div>
                <div class="issue-actions">
                    <input type="checkbox" class="issue-checkbox" id="checkbox-${issue.id}" onchange="toggleIssueSelection('${issue.id}')">
                    <button class="btn-play" onclick="analyzeIssue('${issue.id}')" id="play-${issue.id}">
                        Analyze
                    </button>
                </div>
            </div>
        `).join('');
        console.log('✅ Issues rendered successfully');
    },

    renderSingleAnalysis(analysis, plan, issueId) {
        document.getElementById('analysisSection').style.display = 'block';
        document.getElementById('analysisLoading').style.display = 'none';
        document.getElementById('analysisGrid').style.display = 'grid';

        // Update title
        document.querySelector('#analysisSection .section-title').textContent = `Analysis Results - Issue #${issueId}`;

        // Display feasibility analysis
        const feasibilityContent = document.getElementById('feasibilityContent');
        const score = analysis?.feasibility_score || 0;
        const scoreDeg = (score / 100) * 360;

        feasibilityContent.innerHTML = `
            <div class="score-display">
                <div class="score-circle" style="--score-deg: ${scoreDeg}deg">
                    <div class="score-text">${score}%</div>
                </div>
                <div>
                    <div style="font-weight: 600; margin-bottom: 8px; font-size: 1.125rem;">Feasibility Score</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">
                        ${score >= 70 ? '✅ High feasibility' : score >= 40 ? '⚠️ Medium feasibility' : '❌ Low feasibility'}
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Complexity Score</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">
                        ${analysis?.complexity_score || 0}/100
                        <span style="color: ${analysis?.complexity_score >= 70 ? 'var(--danger)' : analysis?.complexity_score >= 40 ? 'var(--warning)' : 'var(--success)'}">
                            ${analysis?.complexity_score >= 70 ? ' (High)' : analysis?.complexity_score >= 40 ? ' (Medium)' : ' (Low)'}
                        </span>
                    </div>
                </div>
                <div>
                    <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Confidence</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">
                        ${analysis?.confidence || 0}/100
                        <span style="color: ${analysis?.confidence >= 70 ? 'var(--success)' : analysis?.confidence >= 40 ? 'var(--warning)' : 'var(--danger)'}">
                            ${analysis?.confidence >= 70 ? ' (High)' : analysis?.confidence >= 40 ? ' (Medium)' : ' (Low)'}
                        </span>
                    </div>
                </div>
            </div>

            ${analysis?.scope_assessment ? `
                <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                    <div style="font-weight: 600; margin-bottom: 16px; color: var(--text-primary);">Scope Assessment</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-primary); font-size: 0.875rem;">Size</div>
                            <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                <span style="background: rgba(99, 102, 241, 0.1); color: var(--accent-primary); padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                                    ${analysis.scope_assessment.size || 'Unknown'}
                                </span>
                            </div>
                        </div>
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-primary); font-size: 0.875rem;">Impact</div>
                            <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                <span style="background: rgba(99, 102, 241, 0.1); color: var(--accent-primary); padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                                    ${analysis.scope_assessment.impact || 'Unknown'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}

            ${analysis?.technical_analysis?.estimated_files?.length ? `
                <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                    <div style="font-weight: 600; margin-bottom: 12px; color: var(--text-primary);">Files to be Changed</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${analysis.technical_analysis.estimated_files.map(file => `
                            <span style="background: rgba(16, 185, 129, 0.1); color: var(--success); padding: 4px 8px; border-radius: 8px; font-size: 0.75rem; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;">
                                ${file}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${analysis?.technical_analysis?.risks?.length ? `
                <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                    <div style="font-weight: 600; margin-bottom: 12px; color: var(--text-primary);">Potential Risks</div>
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        ${analysis.technical_analysis.risks.map(risk => `
                            <li style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 8px; color: var(--text-secondary); font-size: 0.875rem;">
                                <span style="color: #f59e0b; margin-right: 8px;">⚠️</span>
                                ${risk}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
        `;

        // Display implementation plan
        const planContent = document.getElementById('planContent');
        planContent.innerHTML = `
            <div style="margin-bottom: 24px;">
                <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Summary</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.6;">${plan?.summary || 'No summary available'}</div>
            </div>
            <div style="margin-bottom: 24px;">
                <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Estimated Effort</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.6;">${plan?.estimated_effort || 'Unknown'}</div>
            </div>
            ${plan?.action_plan ? `
                <div>
                    <div style="font-weight: 600; margin-bottom: 16px; color: var(--text-primary);">Action Plan</div>
                    <ul class="plan-steps">
                        ${plan.action_plan.map(step => `
                            <li class="plan-step">
                                <div class="plan-step-number">Step ${step.step}</div>
                                <div class="plan-step-description">${step.description}</div>
                                ${step.files ? `<div style="color: var(--accent-primary); font-size: 0.75rem; margin-top: 8px; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;">Files: ${step.files.join(', ')}</div>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
        `;

        document.getElementById('executeBtn').style.display = 'inline-flex';
    },

    renderMultipleAnalysis(results) {
        const container = document.getElementById('multipleAnalysisGrid');
        container.innerHTML = results.map(result => {
            if (result.error) {
                return `
                    <div class="analysis-card" style="border-color: var(--danger);">
                        <h3>Issue #${result.issue_id} - Error</h3>
                        <div class="message error">${result.error}</div>
                    </div>
                `;
            }

            const analysis = result.analysis;
            const plan = result.plan;
            const score = analysis?.feasibility_score || 0;
            const scoreDeg = (score / 100) * 360;

            return `
                <div class="analysis-card" style="padding: 24px;">
                    <h3 style="margin-bottom: 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 16px;">Issue #${result.issue_id} - Analysis Results</h3>
                    
                    <!-- Two Column Layout for Analysis and Plan -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px;">
                        <!-- Left Column: Feasibility Analysis -->
                        <div>
                            <h4 style="margin-bottom: 16px; color: var(--text-primary);">Feasibility Analysis</h4>
                        <div class="score-display" style="margin-bottom: 16px;">
                            <div class="score-circle" style="--score-deg: ${scoreDeg}deg">
                                <div class="score-text">${score}%</div>
                            </div>
                            <div>
                                <div style="font-weight: 600; margin-bottom: 8px; font-size: 1.125rem;">Feasibility Score</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                    ${score >= 70 ? '✅ High feasibility' : score >= 40 ? '⚠️ Medium feasibility' : '❌ Low feasibility'}
                                </div>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 16px;">
                            <div>
                                <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Complexity Score</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                    ${analysis?.complexity_score || 0}/100
                                    <span style="color: ${analysis?.complexity_score >= 70 ? 'var(--danger)' : analysis?.complexity_score >= 40 ? 'var(--warning)' : 'var(--success)'}">
                                        ${analysis?.complexity_score >= 70 ? ' (High)' : analysis?.complexity_score >= 40 ? ' (Medium)' : ' (Low)'}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Confidence</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                    ${analysis?.confidence || 0}/100
                                    <span style="color: ${analysis?.confidence >= 70 ? 'var(--success)' : analysis?.confidence >= 40 ? 'var(--warning)' : 'var(--danger)'}">
                                        ${analysis?.confidence >= 70 ? ' (High)' : analysis?.confidence >= 40 ? ' (Medium)' : ' (Low)'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        ${analysis?.scope_assessment ? `
                            <div style="margin-bottom: 16px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                                <div style="font-weight: 600; margin-bottom: 12px; color: var(--text-primary);">Scope Assessment</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                    <div>
                                        <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-primary); font-size: 0.875rem;">Size</div>
                                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                            <span style="background: rgba(99, 102, 241, 0.1); color: var(--accent-primary); padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                                                ${analysis.scope_assessment.size || 'Unknown'}
                                            </span>
                                        </div>
                                    </div>
                                    <div>
                                        <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-primary); font-size: 0.875rem;">Impact</div>
                                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                                            <span style="background: rgba(99, 102, 241, 0.1); color: var(--accent-primary); padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                                                ${analysis.scope_assessment.impact || 'Unknown'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}

                        ${analysis?.technical_analysis?.estimated_files?.length ? `
                            <div style="margin-bottom: 16px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                                <div style="font-weight: 600; margin-bottom: 12px; color: var(--text-primary);">Files to be Changed</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                    ${analysis.technical_analysis.estimated_files.map(file => `
                                        <span style="background: rgba(16, 185, 129, 0.1); color: var(--success); padding: 4px 8px; border-radius: 8px; font-size: 0.75rem; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;">
                                            ${file}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}

                        ${analysis?.technical_analysis?.risks?.length ? `
                            <div style="margin-bottom: 16px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                                <div style="font-weight: 600; margin-bottom: 12px; color: var(--text-primary);">Potential Risks</div>
                                <ul style="list-style: none; padding: 0; margin: 0;">
                                    ${analysis.technical_analysis.risks.map(risk => `
                                        <li style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 8px; color: var(--text-secondary); font-size: 0.875rem;">
                                            <span style="color: #f59e0b; margin-right: 8px;">⚠️</span>
                                            ${risk}
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        </div>

                        <!-- Right Column: Implementation Plan -->
                        <div>
                            <h4 style="margin-bottom: 16px; color: var(--text-primary);">Implementation Plan</h4>
                        <div style="margin-bottom: 16px;">
                            <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Summary</div>
                            <div style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.6;">${plan?.summary || 'No summary available'}</div>
                        </div>
                        <div style="margin-bottom: 16px;">
                            <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">Estimated Effort</div>
                            <div style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.6;">${plan?.estimated_effort || 'Unknown'}</div>
                        </div>
                        ${plan?.action_plan ? `
                            <div>
                                <div style="font-weight: 600; margin-bottom: 16px; color: var(--text-primary);">Action Plan</div>
                                <ul class="plan-steps">
                                    ${plan.action_plan.map(step => `
                                        <li class="plan-step">
                                            <div class="plan-step-number">Step ${step.step}</div>
                                            <div class="plan-step-description">${step.description}</div>
                                            ${step.files ? `<div style="color: var(--accent-primary); font-size: 0.75rem; margin-top: 8px; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;">Files: ${step.files.join(', ')}</div>` : ''}
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        </div>
                    </div>

                    <!-- Execute Button -->
                    <div style="text-align: center; padding-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: 24px;">
                        <button class="btn btn-success btn-small" onclick="executeSingleIssue('${result.issue_id}')">
                            Execute Changes
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    },

    // === ISSUE SELECTION FUNCTIONS ===
    toggleIssue(issueId) {
        const checkbox = document.getElementById(`checkbox-${issueId}`);
        if (checkbox.checked) {
            this.state.selectedIssues.add(issueId);
        } else {
            this.state.selectedIssues.delete(issueId);
        }
        this.updateSelection();
    },

    toggleSelectAll() {
        const selectAll = document.getElementById('selectAll');
        const checkboxes = document.querySelectorAll('.issue-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
            const issueId = checkbox.id.replace('checkbox-', '');
            if (selectAll.checked) {
                this.state.selectedIssues.add(issueId);
            } else {
                this.state.selectedIssues.delete(issueId);
            }
        });
        
        this.updateSelection();
    },

    updateSelection() {
        const count = document.getElementById('selectedCount');
        const btn = document.getElementById('analyzeAllBtn');
        
        if (this.state.selectedIssues.size > 0) {
            count.textContent = `${this.state.selectedIssues.size} selected`;
            count.style.display = 'inline-block';
            btn.style.display = 'inline-flex';
        } else {
            count.style.display = 'none';
            btn.style.display = 'none';
        }
    },

    // === UTILITY FUNCTIONS ===
    setIssuesLoading() {
        document.getElementById('issuesList').innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                <div class="spinner" style="margin: 0 auto 16px;"></div>
                <h3>Fetching Repository Issues</h3>
                <p>Please wait while we retrieve the issues from ${this.state.currentRepoUrl}</p>
            </div>
        `;
    },

    setLoading(btn, text) {
        btn.disabled = true;
        btn.innerHTML = `<div class="spinner" style="width: 12px; height: 12px;"></div> ${text}`;
    },

    clearLoading(btn, html) {
        btn.disabled = false;
        btn.innerHTML = html;
    },

    showSection(id) {
        document.getElementById(id).style.display = 'block';
    },

    hideSection(id) {
        document.getElementById(id).style.display = 'none';
    },

    showElement(id) {
        document.getElementById(id).style.display = 'flex';
    },

    hideElement(id) {
        document.getElementById(id).style.display = 'none';
    },

    showMessage(text, type) {
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.innerHTML = `<strong>${type === 'error' ? 'Error' : 'Success'}:</strong> ${text}`;
        document.querySelector('.container').insertBefore(message, document.querySelector('.container').firstChild);
        setTimeout(() => message.remove(), 5000);
    }
};

// === GLOBAL FUNCTIONS FOR HTML ONCLICK HANDLERS ===
// These functions bridge the HTML onclick handlers to the App object methods

function fetchIssues() {
    App.fetchIssues();
}

function analyzeIssue(issueId) {
    App.analyzeSingle(issueId);
}

function analyzeMultipleIssues() {
    App.analyzeMultiple();
}

function executeChanges() {
    App.execute();
}

function executeSingleIssue(issueId) {
    App.executeSingle(issueId);
}

function executeMultipleIssues() {
    console.log('Execute multiple issues:', Array.from(App.state.selectedIssues));
}

function toggleIssueSelection(issueId) {
    App.toggleIssue(issueId);
}

function toggleSelectAll() {
    App.toggleSelectAll();
}

function showError(message) {
    App.showMessage(message, 'error');
}

function showSuccess(message) {
    App.showMessage(message, 'success');
}

// === EVENT LISTENERS ===
document.addEventListener('DOMContentLoaded', () => {
    // Enter key support for repo URL input
    document.getElementById('repoUrl').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            fetchIssues();
        }
    });
    
    // Initialize global variables for compatibility
    window.currentRepoUrl = '';
    window.issues = [];
    window.selectedIssues = new Set();
}); 