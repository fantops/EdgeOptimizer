# Contributing to EdgeOptimizer

Thank you for your interest in contributing to EdgeOptimizer's power comparison research! Please follow these guidelines:

## 🤝 How to Contribute

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow modular architecture**: Use existing components when possible
4. **Add power monitoring**: Include power analysis for new features
5. **Test thoroughly**: Run power comparison tests
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**

## 🔧 Development Guidelines

### **Power Comparison Focus**
- Use the modular component system (`optimizer/`)
- Add comprehensive logging with `logging_config.py`
- Include power monitoring for new inference methods
- Follow existing configuration patterns
- Add tests to `experiments/` directory

### **Code Quality**
- Follow PEP8 for Python code
- Add docstrings and comments where helpful
- Write clear, concise commit messages
- Ensure your code passes all tests and lints

### **Testing Requirements**
- Run power comparison experiments to validate changes
- Test both local and cloud inference paths
- Verify power monitoring accuracy
- Check configuration loading and validation

## 🧪 Power Comparison Guidelines

### **Adding New Experiments**
- Place new experiment scripts in `experiments/` directory
- Use the `PowerConsumptionMonitor` for consistent power analysis
- Follow existing result logging patterns
- Include both local and cloud comparison when applicable

### **Extending Power Monitoring**
- Use the centralized `logging_config.py` system
- Save results to appropriate log directories (`power_analysis/`, `experiments/`)
- Include metadata for experiment reproducibility
- Document power measurement methodology

## 🐛 Issues

- Search for existing issues before opening a new one
- Provide detailed steps to reproduce bugs
- Include power comparison results when relevant
- Specify your hardware configuration for power-related issues

## 💬 Questions?

Open an issue or start a discussion! We're particularly interested in:
- Power efficiency improvements
- New inference optimization techniques
- Cross-platform power monitoring enhancements
- Experiment methodology suggestions
