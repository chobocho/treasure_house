// 슬라이드 p11-v10-ns-rules — 한 파일에 하나, 블록과 섞지 않기, C# 10.0
#if TYPEFIRST
class Early { }
#endif
namespace Shop;

#if TWICE
namespace Shop.More;
#endif
#if MIX
namespace Inner { class Deep { } }
#endif

class App
{
    static void Main() =>
        System.Console.WriteLine(typeof(App).FullName);
}
