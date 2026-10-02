// 슬라이드 p8-v7-exprbody-il — 블록 본문과 식 본문의 IL, C# 7.0
using System;
using System.Linq;
using System.Reflection;

class App
{
    int x = 21;

    int Block() { return x * 2; }
    int Arrow() => x * 2;

    int PBlock { get { return x; } }
    int PArrow { get => x; }

    static string IL(string name)
    {
        MethodInfo m = typeof(App).GetMethod(name,
            BindingFlags.Instance | BindingFlags.NonPublic);
        return string.Join(" ", m.GetMethodBody().GetILAsByteArray()
            .Select(b => b.ToString("X2")));
    }

    static void Main()
    {
        Console.WriteLine("Block   " + IL("Block"));
        Console.WriteLine("Arrow   " + IL("Arrow"));
        Console.WriteLine("PBlock  " + IL("get_PBlock"));
        Console.WriteLine("PArrow  " + IL("get_PArrow"));
    }
}
