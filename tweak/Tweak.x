// ═══════════════════════════════════════════════════════════════════════════════
//  Tweak.x — FreeFire Injector para Filza (app "3105")
//  Autor: Lopes
//  Build: Theos (Logos preprocessor)
//
//  O que faz:
//    • Adiciona um botao flutuante "🎮 Injetar FF" sobre toda a UI do Filza
//    • Quando clicado, localiza o container do Free Fire (/var/mobile/Containers/...)
//    • Cria o arquivo assetindexer.H5ak1... no caminho correto
//    • Mostra alerta de sucesso ou erro
// ═══════════════════════════════════════════════════════════════════════════════

#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>

// ── Configuracoes ─────────────────────────────────────────────────────────────

// Bundle ID do jogo alvo
static NSString *const kTargetBundle = @"com.dts.freefireth";

// Caminho relativo ao container do jogo (sem o UUID)
static NSString *const kRelativePath =
    @"/Documents/contentcache/Compulsory/ios/gameassetbundles/avatar/"
     "assetindexer.H5ak1JM1Eck~2FxRcJrEp~2FMzeuqmY~3D";

// Conteudo que sera escrito no arquivo (pode ser bytes, string, etc.)
static NSString *const kFileContent = @"LOPES_INJECTED_OK";

// ── Helper: Encontra container do Free Fire ───────────────────────────────────

static NSString *FFContainerPath(void) {
    NSString *appsBase = @"/var/mobile/Containers/Data/Application";
    NSFileManager *fm  = [NSFileManager defaultManager];
    NSError *err       = nil;

    NSArray<NSString *> *uuids = [fm contentsOfDirectoryAtPath:appsBase error:&err];
    if (err || !uuids) return nil;

    for (NSString *uuid in uuids) {
        // Cada pasta tem um .plist escondido com o bundle ID
        NSString *metaPath = [appsBase stringByAppendingPathComponent:
            [uuid stringByAppendingPathComponent:
                @".com.apple.mobile_container_manager.metadata.plist"]];

        NSDictionary *meta = [NSDictionary dictionaryWithContentsOfFile:metaPath];
        if ([meta[@"MCMMetadataIdentifier"] isEqualToString:kTargetBundle]) {
            return [appsBase stringByAppendingPathComponent:uuid];
        }
    }
    return nil;
}

// ── Helper: Exibe alerta ──────────────────────────────────────────────────────

static void ShowAlert(NSString *title, NSString *message) {
    dispatch_async(dispatch_get_main_queue(), ^{
        UIAlertController *alert =
            [UIAlertController alertControllerWithTitle:title
                                               message:message
                                        preferredStyle:UIAlertControllerStyleAlert];

        [alert addAction:[UIAlertAction actionWithTitle:@"OK"
                                                  style:UIAlertActionStyleDefault
                                                handler:nil]];

        // Sobe na hierarquia ate encontrar um VC que pode apresentar
        UIViewController *root =
            [UIApplication sharedApplication].keyWindow.rootViewController;
        while (root.presentedViewController)
            root = root.presentedViewController;

        [root presentViewController:alert animated:YES completion:nil];
    });
}

// ── Acao do botao ─────────────────────────────────────────────────────────────

static void InjectFreeFire(void) {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{

        NSString *container = FFContainerPath();

        if (!container) {
            ShowAlert(@"❌ Free Fire nao encontrado",
                      @"Instale o Free Fire no dispositivo e tente novamente.");
            return;
        }

        NSString *targetPath = [container stringByAppendingString:kRelativePath];
        NSString *dirPath    = [targetPath stringByDeletingLastPathComponent];
        NSFileManager *fm    = [NSFileManager defaultManager];
        NSError *err         = nil;

        // Cria pastas intermediarias se nao existirem
        BOOL dirOk = [fm createDirectoryAtPath:dirPath
                   withIntermediateDirectories:YES
                                    attributes:nil
                                         error:&err];
        if (!dirOk || err) {
            ShowAlert(@"❌ Erro ao criar diretorio",
                      err.localizedDescription ?: @"Sem permissao de escrita.");
            return;
        }

        // Escreve o arquivo
        NSData *content = [kFileContent dataUsingEncoding:NSUTF8StringEncoding];
        BOOL written    = [content writeToFile:targetPath
                                   options:NSDataWritingAtomic
                                     error:&err];

        if (written && !err) {
            ShowAlert(@"✅ Injetado com sucesso!",
                      [NSString stringWithFormat:@"Arquivo criado em:\n%@", targetPath]);
        } else {
            ShowAlert(@"❌ Falha na escrita",
                      err.localizedDescription ?: @"Erro desconhecido.");
        }
    });
}

// ── Janela overlay (nivel acima de tudo) ──────────────────────────────────────

static UIWindow   *gOverlayWindow  = nil;
static UIButton   *gInjectButton   = nil;

static void SetupOverlayButton(void) {
    dispatch_async(dispatch_get_main_queue(), ^{
        if (gOverlayWindow) return;  // ja criado

        CGRect screen = [UIScreen mainScreen].bounds;

        // Janela transparente sobre tudo
        if (@available(iOS 13.0, *)) {
            UIWindowScene *scene = nil;
            for (UIScene *s in [UIApplication sharedApplication].connectedScenes) {
                if ([s isKindOfClass:[UIWindowScene class]]) {
                    scene = (UIWindowScene *)s;
                    break;
                }
            }
            gOverlayWindow = [[UIWindow alloc] initWithWindowScene:scene];
        } else {
            gOverlayWindow = [[UIWindow alloc] initWithFrame:screen];
        }

        gOverlayWindow.windowLevel      = UIWindowLevelAlert + 100;
        gOverlayWindow.backgroundColor  = [UIColor clearColor];
        gOverlayWindow.userInteractionEnabled = YES;
        gOverlayWindow.rootViewController     = [UIViewController new];
        gOverlayWindow.rootViewController.view.backgroundColor = [UIColor clearColor];

        // ── Botao ──────────────────────────────────────────────────────────
        CGFloat btnW = 155, btnH = 48;
        CGFloat margin = 16;
        // Posicao inicial: canto inferior direito, acima da tab bar
        CGFloat btnX = screen.size.width  - btnW - margin;
        CGFloat btnY = screen.size.height - btnH - 100;

        gInjectButton = [UIButton buttonWithType:UIButtonTypeCustom];
        gInjectButton.frame = CGRectMake(btnX, btnY, btnW, btnH);

        // Titulo
        [gInjectButton setTitle:@"🎮  Injetar FF" forState:UIControlStateNormal];
        [gInjectButton setTitleColor:[UIColor whiteColor]       forState:UIControlStateNormal];
        [gInjectButton setTitleColor:[UIColor colorWithWhite:1.0 alpha:0.6]
                            forState:UIControlStateHighlighted];
        gInjectButton.titleLabel.font = [UIFont boldSystemFontOfSize:14];

        // Aparencia — laranja vibrante com sombra
        gInjectButton.backgroundColor = [UIColor colorWithRed:0.97
                                                        green:0.41
                                                         blue:0.07
                                                        alpha:1.0];
        gInjectButton.layer.cornerRadius  = 14;
        gInjectButton.layer.masksToBounds = NO;
        gInjectButton.layer.shadowColor   = [UIColor blackColor].CGColor;
        gInjectButton.layer.shadowOpacity = 0.45;
        gInjectButton.layer.shadowRadius  = 8;
        gInjectButton.layer.shadowOffset  = CGSizeMake(0, 4);

        // Animacao de pulso sutil
        CABasicAnimation *pulse = [CABasicAnimation animationWithKeyPath:@"transform.scale"];
        pulse.fromValue   = @1.0;
        pulse.toValue     = @1.04;
        pulse.duration    = 1.2;
        pulse.autoreverses = YES;
        pulse.repeatCount = HUGE_VALF;
        [gInjectButton.layer addAnimation:pulse forKey:@"pulse"];

        // Target-action
        [gInjectButton addTarget:gInjectButton
                          action:@selector(fff_injectTapped)
                forControlEvents:UIControlEventTouchUpInside];

        // Efeito de toque (escurece ao pressionar)
        [gInjectButton addTarget:gInjectButton
                          action:@selector(fff_touchDown)
                forControlEvents:UIControlEventTouchDown | UIControlEventTouchDragEnter];
        [gInjectButton addTarget:gInjectButton
                          action:@selector(fff_touchUp)
                forControlEvents:UIControlEventTouchUpInside
                                | UIControlEventTouchUpOutside
                                | UIControlEventTouchCancel];

        gOverlayWindow.rootViewController.view.frame = screen;
        [gOverlayWindow.rootViewController.view addSubview:gInjectButton];
        gOverlayWindow.hidden = NO;
    });
}

// ── Categoria UIButton com as acoes (evita %hook amplo) ──────────────────────

%hook UIButton

%new
- (void)fff_injectTapped {
    // Animacao de clique
    [UIView animateWithDuration:0.08 animations:^{
        self.transform = CGAffineTransformMakeScale(0.93, 0.93);
    } completion:^(BOOL _) {
        [UIView animateWithDuration:0.12 animations:^{
            self.transform = CGAffineTransformIdentity;
        }];
        InjectFreeFire();
    }];
}

%new
- (void)fff_touchDown {
    [UIView animateWithDuration:0.08 animations:^{
        self.alpha = 0.75;
        self.transform = CGAffineTransformMakeScale(0.95, 0.95);
    }];
}

%new
- (void)fff_touchUp {
    [UIView animateWithDuration:0.12 animations:^{
        self.alpha = 1.0;
        self.transform = CGAffineTransformIdentity;
    }];
}

%end

// ── Ativacao: hook no AppDelegate ─────────────────────────────────────────────

%hook UIApplication

- (BOOL)application:(UIApplication *)app
    didFinishLaunchingWithOptions:(NSDictionary *)opts {

    BOOL r = %orig;

    // Aguarda a UI carregar antes de adicionar o overlay
    dispatch_after(
        dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.8 * NSEC_PER_SEC)),
        dispatch_get_main_queue(),
        ^{ SetupOverlayButton(); }
    );

    return r;
}

%end
