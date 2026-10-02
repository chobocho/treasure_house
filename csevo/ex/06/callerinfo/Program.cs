// 슬라이드 p6-v5-caller-info — 호출자 정보 특성 세 가지, C# 5.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Log(string msg,
        [CallerMemberName] string member = "",
        [CallerFilePath] string path = "",
        [CallerLineNumber] int line = 0)
    {
        Console.WriteLine(msg + " | " + member + " | "
            + path + " | " + line);
    }

    static void Save()
    {
        Log("saving");
    }

    static void Main()
    {
        Log("start");
        Save();
    }
}
