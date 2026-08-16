// Tweak_simple.m
// Versao sem Logos (ObjC puro com method swizzling)
// Usada como fallback quando o preprocessador do Theos nao esta disponivel

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>
#import <objc/runtime.h>

#define kTargetBundle @"com.dts.freefireth"
#define kRelativePath @"/Documents/contentcache/Compulsory/ios/gameassetbundles/avatar/assetindexer.H5ak1JM1Eck~2FxRcJrEp~2FMzeuqmY~3D"
#define kFileContent  @"LOPES_INJECTED_OK"

// ── Helper: localiza container do Free Fire ───────────────────
static NSString *FFContainerPath(void) {
    NSString *base = @"/var/mobile/Containers/Data/Application";
    NSFileManager *fm = [NSFileManager defaultManager];
    for (NSString *uuid in [fm contentsOfDirectoryAtPath:base error:nil]) {
        NSString *meta = [base stringByAppendingPathComponent:
            [uuid stringByAppendingPathComponent:
                @".com.apple.mobile_container_manager.metadata.plist"]];
        NSDictionary *d = [NSDictionary dictionaryWithContentsOfFile:meta];
        if ([d[@"MCMMetadataIdentifier"] isEqualToString:kTargetBundle])
            return [base stringByAppendingPathComponent:uuid];
    }
    return nil;
}

// ── Mostra alerta ─────────────────────────────────────────────
static void ShowAlert(NSString *title, NSString *msg) {
    dispatch_async(dispatch_get_main_queue(), ^{
        UIAlertController *a = [UIAlertController
            alertControllerWithTitle:title message:msg
            preferredStyle:UIAlertControllerStyleAlert];
        [a addAction:[UIAlertAction actionWithTitle:@"OK"
            style:UIAlertActionStyleDefault handler:nil]];
        UIViewController *root = [UIApplication sharedApplication].keyWindow.rootViewController;
        while (root.presentedViewController) root = root.presentedViewController;
        [root presentViewController:a animated:YES completion:nil];
    });
}

// ── Acao do botao ─────────────────────────────────────────────
static void InjectFreeFire(void) {
    dispatch_async(dispatch_get_global_queue(0, 0), ^{
        NSString *container = FFContainerPath();
        if (!container) {
            ShowAlert(@"Free Fire nao encontrado", @"Instale o Free Fire e tente novamente.");
            return;
        }
        NSString *target = [container stringByAppendingString:kRelativePath];
        NSString *dir    = [target stringByDeletingLastPathComponent];
        NSFileManager *fm = [NSFileManager defaultManager];
        [fm createDirectoryAtPath:dir withIntermediateDirectories:YES attributes:nil error:nil];
        NSData *data = [kFileContent dataUsingEncoding:NSUTF8StringEncoding];
        BOOL ok = [data writeToFile:target options:NSDataWritingAtomic error:nil];
        ShowAlert(ok ? @"Injetado!" : @"Falhou",
                  ok ? [NSString stringWithFormat:@"Arquivo criado:\n%@", target]
                     : @"Sem permissao de escrita.");
    });
}

// ── Overlay com botao flutuante ───────────────────────────────
static UIWindow *sOverlay = nil;

static void SetupButton(void) {
    dispatch_async(dispatch_get_main_queue(), ^{
        if (sOverlay) return;
        CGRect screen = UIScreen.mainScreen.bounds;

        if (@available(iOS 13, *)) {
            for (UIScene *s in UIApplication.sharedApplication.connectedScenes) {
                if ([s isKindOfClass:[UIWindowScene class]]) {
                    sOverlay = [[UIWindow alloc] initWithWindowScene:(UIWindowScene*)s];
                    break;
                }
            }
        }
        if (!sOverlay) sOverlay = [[UIWindow alloc] initWithFrame:screen];

        sOverlay.windowLevel = UIWindowLevelAlert + 100;
        sOverlay.backgroundColor = UIColor.clearColor;
        sOverlay.rootViewController = [UIViewController new];
        sOverlay.rootViewController.view.backgroundColor = UIColor.clearColor;

        UIButton *btn = [UIButton buttonWithType:UIButtonTypeCustom];
        CGFloat w = 155, h = 48;
        btn.frame = CGRectMake(screen.size.width - w - 16, screen.size.height - h - 100, w, h);
        [btn setTitle:@"Injetar FF" forState:UIControlStateNormal];
        [btn setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
        btn.titleLabel.font = [UIFont boldSystemFontOfSize:14];
        btn.backgroundColor = [UIColor colorWithRed:.97 green:.41 blue:.07 alpha:1];
        btn.layer.cornerRadius = 14;
        btn.layer.shadowColor = UIColor.blackColor.CGColor;
        btn.layer.shadowOpacity = .45f;
        btn.layer.shadowRadius = 8;
        btn.layer.shadowOffset = CGSizeMake(0, 4);
        [btn addTarget:btn action:@selector(fff_tapped) forControlEvents:UIControlEventTouchUpInside];
        [sOverlay.rootViewController.view addSubview:btn];
        sOverlay.hidden = NO;
    });
}

// ── Swizzle UIButton para adicionar fff_tapped ────────────────
@interface UIButton (FFFInject)
- (void)fff_tapped;
@end

@implementation UIButton (FFFInject)
- (void)fff_tapped { InjectFreeFire(); }
@end

// ── Constructor: roda quando a dylib e carregada ──────────────
__attribute__((constructor))
static void FFInjectorInit(void) {
    // Aguarda a UI principal estar pronta
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2.0 * NSEC_PER_SEC)),
                   dispatch_get_main_queue(), ^{
        SetupButton();
    });
}
