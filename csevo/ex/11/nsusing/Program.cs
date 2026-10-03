// 슬라이드 p11-v10-ns-using — namespace X; 뒤의 using, C# 10.0
#if BEFORE
using Data;                         // file level: global Data
#endif
namespace App;
#if !BEFORE
using Data;                         // inside App: App.Data first
#endif

class Program
{
    static void Main() =>
        System.Console.WriteLine(new Store().Where);
}
