// 슬라이드 p0-runtime — C# 1 로 컴파일해도 런타임은 .NET 10, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        ArrayList list = new ArrayList();
        list.Add("C# 1");
        list.Add(Environment.Version.ToString());
        foreach (string s in list)
        {
            Console.WriteLine(s);
        }
    }
}
