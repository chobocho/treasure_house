// 슬라이드 p3-v2-global — global:: 로 맨 바깥에서 찾기, C# 2.0
namespace Shop
{
    class System { }                     // still here

    class App
    {
        static void Main()
        {
            global::System.Console.WriteLine("hello");
            global::System.Console.WriteLine(typeof(System).FullName);
        }
    }
}
