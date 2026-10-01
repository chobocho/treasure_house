// 슬라이드 p3-v2-extern-alias — extern alias, C# 2.0
extern alias Con;                    // defined by: -r:Con=<dll>

class App
{
    static void Main()
    {
        Con::System.Console.WriteLine("via the alias Con");
        System.Console.WriteLine("via the global alias");
        System.Console.WriteLine(typeof(Con::System.Console) ==
            typeof(global::System.Console));
    }
}
