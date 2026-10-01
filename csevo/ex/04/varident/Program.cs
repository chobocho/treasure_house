// 슬라이드 p4-v3-var-contextual — var 는 키워드가 아니다, C# 3.0
using System;

class App
{
    static int var(int x) { return x * 10; }

    static void Main()
    {
        int var = 4;               // a local named var
        Console.WriteLine(var + 1);
        Console.WriteLine(App.var(var));
    }
}
