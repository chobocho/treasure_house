// 슬라이드 p3-v2-nullable-nested — nullable 의 nullable 은 없다, C# 2.0
using System;

class App
{
    static void Main()
    {
        Nullable<Nullable<int>> x = new Nullable<Nullable<int>>();
        Nullable<string> s = null;
        Console.WriteLine(x.HasValue + " " + s.HasValue);
    }
}
