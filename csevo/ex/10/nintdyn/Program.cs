// 슬라이드 p10-v9-nint-dyn — dynamic 은 nint 의 연산자를 모른다, C# 9.0
using System;

class App
{
    static void Main()
    {
        nint x = 2;
        nint y = x + x;
        dynamic d = x;
        Console.WriteLine(y + " " + d.GetType().Name);
        try
        {
            nint z = d + x;
            Console.WriteLine("dynamic: " + z);
        }
        catch (Exception e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.Message);
        }
    }
}
