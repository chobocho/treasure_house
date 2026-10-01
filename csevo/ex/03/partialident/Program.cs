// 슬라이드 p3-v2-partial-ident — partial 은 문맥 키워드, C# 1.0
using System;

class App
{
    static int partial(int x) { return x * 2; }

    static void Main()
    {
        int partial = 21;
        Console.WriteLine(App.partial(partial));
    }
}
