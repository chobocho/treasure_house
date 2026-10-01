// 슬라이드 p4-v3-lambda-later — static 람다가 지역 변수를 잡으면, C# 9
using System;

class App
{
    static void Main()
    {
        int k = 1;
        Func<int, int> add = static x => x + k;
        Console.WriteLine(add(1));
    }
}
