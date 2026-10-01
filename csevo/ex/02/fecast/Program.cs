// 슬라이드 p2-v1-fecast — foreach 에 숨은 캐스트, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        ArrayList names = new ArrayList();
        names.Add("kim");
        names.Add("lee");
        names.Add(7);                    // an int sneaks in

        foreach (string s in names)      // (string)e.Current each time
            Console.WriteLine(s.ToUpper());
    }
}
