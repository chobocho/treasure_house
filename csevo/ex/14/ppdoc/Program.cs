// 슬라이드 p14-v13-pp-doc — 문서 주석은 구현 쪽이 이긴다, C# 13.0
using System;
using System.IO;
using System.Linq;

/// <summary>My type</summary>
partial class C
{
    /// <summary>Definition part comment</summary>
    /// <returns>Return value comment</returns>
    public partial int Prop { get; set; }

    /// <summary>Implementation part comment</summary>
    public partial int Prop { get => 1; set { } }
}

class App
{
    static void Main()
    {
        // csrun was given -doc:bin/doc.xml
        foreach (var line in File.ReadAllLines("bin/doc.xml")
                     .Where(l => l.Contains("<member")
                         || l.Contains("<summary")
                         || l.Contains("<returns")))
            Console.WriteLine(line.Trim());
    }
}
