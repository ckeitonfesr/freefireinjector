#import <UIKit/UIKit.h>
#import <objc/runtime.h>

@implementation NSObject (TweakFilesTab)

- (void)tweak_layoutSubviews {
    // Chama o original
    [self tweak_layoutSubviews];
    
    UIView *view = (UIView *)self;
    // Procura por UILabel dentro do botao
    for (UIView *subview in view.subviews) {
        if ([subview isKindOfClass:[UILabel class]]) {
            UILabel *label = (UILabel *)subview;
            NSString *text = label.text;
            // Se o texto for "Files" ou a chave original, desativa e esconde
            if ([text isEqualToString:@"Files"] || 
                [text isEqualToString:@"tab.files"] || 
                [text isEqualToString:@"Arquivos"]) {
                
                view.hidden = YES;
                view.userInteractionEnabled = NO;
                view.alpha = 0;
                view.frame = CGRectZero; // Encolhe para nao ocupar espaco
            }
        }
    }
}

@end

__attribute__((constructor))
static void InjectInit(void) {
    // Hook na classe interna do iOS que representa os botoes da Tab Bar
    Class targetClass = NSClassFromString(@"UITabBarButton");
    if (!targetClass) return;
    
    Method orig = class_getInstanceMethod(targetClass, @selector(layoutSubviews));
    Method swiz = class_getInstanceMethod(NSClassFromString(@"NSObject"), @selector(tweak_layoutSubviews));
    
    if (orig && swiz) {
        method_exchangeImplementations(orig, swiz);
    }
}
