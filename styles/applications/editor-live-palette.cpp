// KTextEditor owns a separate repository and renderer; a Qt palette alone cannot update it.
#include <QApplication>
#include <KTextEditor/Editor>
#include <KTextEditor/Document>
#include <KTextEditor/View>
#include <KSyntaxHighlighting/Repository>
#include <QFile>
#include <QTextStream>
#include <QTimer>
static void apply_view(KTextEditor::View *view) {
    view->setConfigValue(QStringLiteral("theme"),QStringLiteral("Obsidian"));
    if(!qEnvironmentVariable("OBSIDIAN_EDITOR_TEST_OUTPUT").isEmpty()) {
        QFile output(qEnvironmentVariable("OBSIDIAN_EDITOR_TEST_OUTPUT"));
        if(output.open(QIODevice::WriteOnly))QTextStream(&output)<<view->configValue(QStringLiteral("background-color")).value<QColor>().name();
    }
}
static void attach_document(KTextEditor::Document *document) {
    QObject::connect(document,&KTextEditor::Document::viewCreated,document,[](auto,auto view){
        QTimer::singleShot(0,view,[view]{apply_view(view);});
    });
    for(auto view:document->views())apply_view(view);
}
extern "C" void obsidian_editor_initialize() {
    static bool initialized=false;if(initialized)return;initialized=true;
    auto editor=KTextEditor::Editor::instance();
    QObject::connect(editor,&KTextEditor::Editor::documentCreated,editor,[](auto,auto document){attach_document(document);});
    for(auto document:editor->documents())attach_document(document);
}
extern "C" void obsidian_editor_refresh() {
    auto editor=KTextEditor::Editor::instance();
    auto &repository=const_cast<KSyntaxHighlighting::Repository &>(editor->repository());
    repository.reload();
    for(auto widget:QApplication::allWidgets())
        if(auto view=qobject_cast<KTextEditor::View *>(widget))apply_view(view);
}
