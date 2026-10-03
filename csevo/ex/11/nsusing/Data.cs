// 슬라이드 p11-v10-ns-using — 이름이 같은 두 네임스페이스, C# 10.0
namespace Data
{
    class Store { public string Where => "Data.Store"; }
}

namespace App.Data
{
    class Store { public string Where => "App.Data.Store"; }
}
