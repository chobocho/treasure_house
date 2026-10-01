// 슬라이드 p3-v2-global-why — 같은 이름이 System 을 가리면, C# 2.0
namespace Shop
{
    class System { }                     // an unlucky name

    class App
    {
        static void Main()
        {
            System.Console.WriteLine("hello");
        }
    }
}
