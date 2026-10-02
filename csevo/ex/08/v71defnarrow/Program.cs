// 슬라이드 p8-v7_1-default-narrow — 7.1 뒤에 막힌 default, C# 7.1
using System;

class App
{
    static bool IsDefault<T>(T t) => t == default;   // VS2019 16.4

    static void Main()
    {
        object o = 1;
        int i = default ?? 1;                        // fixed in 7.2
        Console.WriteLine(o is default);             // VS2017 15.7
        switch (o)
        {
            case default:                            // VS2017 15.7
                break;
        }
        string s = default as string;                // VS2019 16.4
        using (default) { }                          // VS2019 16.4
    }
}
