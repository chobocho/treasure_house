// 슬라이드 p3-v2-default-t — default(T) 로 '없음' 돌려주기, C# 2.0
using System;

class App
{
    static T FirstOrDefault<T>(T[] xs)
    {
        if (xs.Length == 0)
        {
            return default(T);            // 0, null, false ... by T
        }
        return xs[0];
    }

    static void Main()
    {
        Console.WriteLine(FirstOrDefault(new int[0]));
        Console.WriteLine(FirstOrDefault(new string[0]) == null);
        Console.WriteLine(FirstOrDefault(new bool[0]));
        Console.WriteLine(FirstOrDefault(new int[] { 7 }));
    }
}
